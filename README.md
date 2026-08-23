# Cloud Storage Service — MVP

Google Drive–style file storage & sharing app. Stack: **React + Vite + Tailwind**
(frontend, starts Day 8), **FastAPI** (backend), **Supabase Postgres** (database),
**Supabase Storage** (files). Built against the 14-day plan in the project spec.

## Day 1 status — Requirement Analysis & Database Design ✅

- [x] Feature scope reviewed, MVP vs Phase 2 finalized (see spec)
- [x] ER diagram designed — `docs/ER_DIAGRAM.md` (8 core tables)
- [x] Storage provider decided: **Supabase Storage** (keeps DB, auth, and storage on one platform for the MVP)
- [x] Git repo initialized
- [x] Backend project scaffolded (`backend/app/...`) with SQLAlchemy models for every table
- [x] FastAPI boots with a `/health` check (no feature routes yet — those start Day 2)

Nothing beyond Day 1 has been built: no auth, no upload flow, no frontend. Those land
on their scheduled days per `docs/ER_DIAGRAM.md`'s companion plan in the spec.

## Project structure

```
backend/
├── app/
│   ├── main.py          # FastAPI app, health check only (Day 1)
│   ├── core/
│   │   ├── config.py         # env-driven settings (Supabase, DB, JWT)
│   │   ├── database.py       # SQLAlchemy engine/session
│   │   └── supabase_client.py# Supabase Storage client
│   ├── models/           # SQLAlchemy models = the ER diagram, 8 tables
│   ├── schemas/           # Pydantic schemas (empty until Day 2)
│   ├── routes/             # API routers (empty until Day 2)
│   ├── services/            # business logic (empty until Day 2)
│   └── utils/                 # helpers (empty until Day 2)
├── requirements.txt
└── .env.example
docs/
└── ER_DIAGRAM.md        # Mermaid ER diagram + design notes
```

## Setting up Supabase (Day 1)

1. Create a project at [supabase.com](https://supabase.com) (free tier is fine for MVP dev).
2. **Project Settings → API**: copy the `Project URL`, `anon public` key, and
   `service_role` key into `backend/.env` (`SUPABASE_URL`, `SUPABASE_ANON_KEY`,
   `SUPABASE_SERVICE_ROLE_KEY`).
3. **Project Settings → Database**: copy the connection string (use the *connection
   pooling* URI) into `DATABASE_URL` in `backend/.env`.
4. **Storage**: create a bucket named `files` (matches `SUPABASE_STORAGE_BUCKET` in
   `.env`) — this is wired up for real on Day 3.
5. Tables are not created yet — that happens once Alembic migrations are added
   (Day 2), so the models are reviewed/confirmed first.

## Running the backend locally

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in your Supabase values
uvicorn app.main:app --reload
```

Visit `http://localhost:8000/health` → `{"status": "healthy", "env": "development"}`.
Visit `http://localhost:8000/docs` for the (currently empty) auto-generated API docs.

## Next up (Day 2)

Backend setup & authentication: Alembic migrations to actually create the tables in
Supabase, user registration/login, password hashing, JWT access + refresh tokens,
and auth middleware. Not started yet — waiting on your confirmation of Day 1.
