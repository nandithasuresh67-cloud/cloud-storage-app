"""
Fails fast (or at least warns loudly) on the environment-variable mistakes
that are easy to make and dangerous to miss - the actual point of "Day 7:
environment variable setup" beyond just having a .env.example file.
"""

import logging
import sys

from app.core.config import Settings

logger = logging.getLogger("app.startup")


def check_environment(settings: Settings) -> None:
    problems: list[str] = []
    warnings: list[str] = []

    if settings.ENV == "production":
        if settings.JWT_SECRET_KEY == "change-me":
            problems.append(
                "JWT_SECRET_KEY is still the default 'change-me' value in production. "
                "Set a real random secret (e.g. `openssl rand -hex 32`)."
            )
        if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
            problems.append(
                "SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY are not set in production - "
                "file upload and storage endpoints will return 502s until they are."
            )
        if not settings.DATABASE_URL:
            problems.append("DATABASE_URL is not set in production - every DB-backed endpoint will fail.")
        if any("localhost" in origin for origin in settings.CORS_ORIGINS):
            warnings.append(
                f"CORS_ORIGINS still includes a localhost entry in production: {settings.CORS_ORIGINS}. "
                "Remove it unless you really mean to allow local dev origins to call the prod API."
            )

    if not settings.DATABASE_URL:
        warnings.append("DATABASE_URL is not set - every endpoint that touches the database will fail with a clear error.")

    for w in warnings:
        logger.warning("Startup config warning: %s", w)

    if problems:
        message = "Refusing to start with an unsafe production configuration:\n" + "\n".join(f"  - {p}" for p in problems)
        logger.error(message)
        # Fail loudly rather than silently serving a broken/insecure API -
        # a misconfigured prod deploy that "looks up" but 502s on every
        # real request is worse than one that never started.
        print(message, file=sys.stderr)
        sys.exit(1)
