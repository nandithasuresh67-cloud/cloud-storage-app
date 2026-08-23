"""
TEMPORARY auth stand-in.

Real JWT authentication (register/login/access+refresh tokens) is its own
step in the plan and hasn't been built yet - the frontend day got built
ahead of it. Until that lands, every endpoint that needs "the current
user" reads a plain `X-User-Id` header instead of a verified JWT.

This is intentionally NOT secure - anyone can claim to be any user id by
setting the header. It exists only so the upload flow can be built and
tested against a real users/files foreign key relationship today.

Replace get_current_user_id's body with real JWT verification (and delete
this docstring) when auth is implemented, and remove X-User-Id support
everywhere it's referenced.
"""

import uuid

from fastapi import Header, HTTPException, status


def get_current_user_id(x_user_id: str = Header(..., alias="X-User-Id")) -> uuid.UUID:
    try:
        return uuid.UUID(x_user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-User-Id header must be a valid UUID (temporary stand-in for real auth).",
        )
