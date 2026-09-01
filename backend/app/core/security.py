"""
Password hashing.

Uses the `bcrypt` library directly instead of going through passlib's
CryptContext. passlib 1.7.4's bcrypt backend-detection code reads
`bcrypt.__about__.__version__`, which was removed in bcrypt 5.x - this
throws "AttributeError: module 'bcrypt' has no attribute '__about__'"
(followed by a confusing "password cannot be longer than 72 bytes" error
that's really just that failed detection falling through to a broken
code path) on any environment that resolves bcrypt>=4.1 despite
requirements.txt pinning an older version, which happens more often than
it should depending on platform/resolver. Calling bcrypt directly avoids
relying on that detection code at all.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Literal

import bcrypt
from jose import JWTError, jwt

from app.core.config import get_settings

_BCRYPT_MAX_BYTES = 72  # bcrypt's own hard limit


def hash_password(plain: str) -> str:
    password_bytes = plain.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    password_bytes = plain.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    try:
        return bcrypt.checkpw(password_bytes, hashed.encode("utf-8"))
    except ValueError:
        # Malformed/foreign hash format - treat as "does not match" rather than raising.
        return False


class InvalidTokenError(Exception):
    """Raised for any malformed, expired, or wrong-type token."""


def create_token(user_id: uuid.UUID, token_type: Literal["access", "refresh"], expires_delta: timedelta) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    claims = {
        "sub": str(user_id),
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
        # Random per-token id: without this, two tokens issued for the same
        # user within the same second (iat has 1-second resolution) would
        # be byte-identical, making "rotation" on refresh undetectable and
        # collapsing what should be two distinct sessions into one.
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(claims, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str, expected_type: Literal["access", "refresh"]) -> uuid.UUID:
    """Returns the user id encoded in the token, or raises InvalidTokenError."""
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError as exc:
        raise InvalidTokenError(str(exc)) from exc

    if payload.get("type") != expected_type:
        raise InvalidTokenError(f"Expected a {expected_type} token, got {payload.get('type')!r}.")

    sub = payload.get("sub")
    if not sub:
        raise InvalidTokenError("Token is missing a subject claim.")

    try:
        return uuid.UUID(sub)
    except ValueError as exc:
        raise InvalidTokenError("Token subject is not a valid user id.") from exc
