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

import bcrypt

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
