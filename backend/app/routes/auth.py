import uuid
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.deps import get_current_user_id
from app.core.security import InvalidTokenError, create_token, decode_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()

ACCESS_COOKIE = "access_token"
REFRESH_COOKIE = "refresh_token"


def _set_auth_cookies(response: Response, user_id: uuid.UUID) -> None:
    """
    HttpOnly cookies rather than a token in the JSON body + localStorage:
    JavaScript can never read these, so a successful XSS on the frontend
    can't just read the token out of storage and exfiltrate it. The
    trade-off is CSRF exposure, mitigated by SameSite (Lax in dev, since
    the frontend and backend are different ports on localhost which
    browsers treat as "same-site"; None+Secure in production, since a
    real deployment will usually have the frontend and API on different
    domains, which requires SameSite=None to send the cookie at all - and
    None requires Secure, i.e. HTTPS only).
    """
    secure = settings.ENV == "production"
    samesite = "none" if secure else "lax"

    access_token = create_token(user_id, "access", timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    refresh_token = create_token(user_id, "refresh", timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))

    response.set_cookie(
        ACCESS_COOKIE,
        access_token,
        httponly=True,
        secure=secure,
        samesite=samesite,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    response.set_cookie(
        REFRESH_COOKIE,
        refresh_token,
        httponly=True,
        secure=secure,
        samesite=samesite,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        # Scoped to only the refresh endpoint - defense in depth, so a
        # stolen access-token-reading exploit path doesn't automatically
        # get the longer-lived refresh token sent along on every request too.
        path="/auth/refresh",
    )


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, response: Response, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists.")

    user = User(email=payload.email, full_name=payload.full_name, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)

    _set_auth_cookies(response, user.id)
    return user


@router.post("/login", response_model=UserOut)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()

    # Same error for "no such user" and "wrong password" - distinguishing
    # them lets an attacker enumerate which emails have accounts.
    invalid_credentials = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password."
    )
    if user is None or user.password_hash is None:
        raise invalid_credentials
    if not verify_password(payload.password, user.password_hash):
        raise invalid_credentials
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account has been deactivated.")

    _set_auth_cookies(response, user.id)
    return user


@router.post("/refresh", response_model=UserOut)
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get(REFRESH_COOKIE)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token provided.")

    try:
        user_id = decode_token(token, expected_type="refresh")
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid or expired refresh token: {exc}"
        ) from exc

    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account no longer exists or is inactive.")

    # Issues a fresh pair (rotation) rather than just a new access token -
    # narrows the window a leaked refresh token stays useful for.
    _set_auth_cookies(response, user.id)
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response):
    response.delete_cookie(ACCESS_COOKIE, path="/")
    response.delete_cookie(REFRESH_COOKIE, path="/auth/refresh")
    return None


@router.get("/me", response_model=UserOut)
def me(db: Session = Depends(get_db), user_id: uuid.UUID = Depends(get_current_user_id)):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        # Token/header was valid but the user row is gone - shouldn't
        # normally happen, but fail clearly rather than 500.
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer exists.")
    return user
