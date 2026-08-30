# Backend deployment image. Works for Render, Fly.io, or any other
# Docker-based host - both platforms are covered by this one image rather
# than needing separate buildpacks.
FROM python:3.12-slim

WORKDIR /app

# No apt-get step needed: psycopg2-binary ships a self-contained wheel with
# libpq bundled in, so there's nothing here that needs compiling (verified
# by actually installing and importing it, not assumed from the package name).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Render and Fly.io both inject $PORT at runtime and expect the app to
# bind to it - hardcoding 8000 here would work locally but fail on either
# platform, since they route traffic to whatever port they told the
# container to use, not always 8000.
ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
