from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"service": settings.APP_NAME, "status": "ok"}


@app.get("/health")
def health():
    """
    Basic liveness check for Day 1. Does not yet touch the database —
    DB connectivity gets its own check once auth lands on Day 2.
    """
    return {"status": "healthy", "env": settings.ENV}


# Feature routers (auth, files, folders, shares) are added starting Day 2
# as each API is implemented, per the project's 14-day plan.
