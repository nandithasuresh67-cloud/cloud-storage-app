"""
Authentication dependency.

Primary mechanism (production and dev alike): a JWT access token read from
an HttpOnly cookie, set by POST /auth/login or /auth/register - see
app/routes/auth.py. Falling back to an `Authorization: Bearer <token>`
header also works, for API clients (Postman, mobile apps) that don't use
cookies.

Dev/test-only fallback: if neither is present, and ENV is NOT
"production", a plain `X-User-Id: <uuid>` header is accepted as-is. This
existed as the ONLY auth mechanism before real auth was built (Days 3-7),
and is kept now purely so that large existing test suite and the Postman
collection built against it don't all need rewriting. It is a real
security hole if it ever ran in production - anyone could claim to be any
user - so it is hard-disabled whenever ENV=="production", not just
discouraged in a docstring.
"""

import uuid

from fastapi import HTTPException, Request, status

from app.core.config import get_settings
from app.core.security import InvalidTokenError, decode_token


def get_current_user_id(request: Request) -> uuid.UUID:
    settings = get_settings()

    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[len("Bearer ") :]

    if token:
        try:
            return decode_token(token, expected_type="access")
        except InvalidTokenError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid or expired session: {exc}"
            ) from exc

    if settings.ENV != "production":
        x_user_id = request.headers.get("X-User-Id")
        if x_user_id:
            try:
                return uuid.UUID(x_user_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="X-User-Id header must be a valid UUID (dev-only auth fallback).",
                )

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated.")
