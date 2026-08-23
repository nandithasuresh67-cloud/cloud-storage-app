# Cloud Storage Service — MVP

Google Drive–style file storage & sharing app. Stack: **React + Vite + Tailwind**
(frontend, starts Day 8), **FastAPI** (backend), **Supabase Postgres** (database),
**Supabase Storage** (files). Built against the 14-day plan in the project spec.

## Day 2 status — Frontend Setup & Backend Connection ✅

- [x] React + Vite + Tailwind CSS frontend scaffolded in `frontend/`
- [x] Project structure per spec section 11 (`components/`, `pages/`, `services/`, `hooks/`, `styles/`)
- [x] App shell: sidebar (My Drive / Shared / Starred / Trash), header, breadcrumb, empty states — no advanced features yet
- [x] Axios client (`src/services/api.js`) reads backend URL from `VITE_API_URL`
- [x] Live connection badge in the header, backed by a React Query hook hitting the backend's `/health` endpoint
- [x] Verified: production build passes, lint passes (0 warnings), backend `/health` reachable from the frontend with CORS confirmed working (preflight + actual GET)

Backend was not modified this step — only read from. No auth, no file upload, no real data yet; those come on their scheduled days.

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
frontend/
├── src/
│   ├── main.jsx           # React root: QueryClientProvider + BrowserRouter
│   ├── App.jsx             # Route table
│   ├── index.css            # Tailwind entry point
│   ├── components/           # Layout, Sidebar, Header, Breadcrumb, EmptyState, ConnectionStatus
│   ├── pages/                  # Dashboard (My Drive), Shared, Starred, Trash — all placeholders
│   ├── services/                 # api.js (Axios client), health.js
│   └── hooks/                      # useHealth.js (React Query)
├── vite.config.js
└── .env.example
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
   (Day 2 backend work, not yet done), so the models are reviewed/confirmed first.

## Running everything locally

Two terminals — backend first, then frontend.

**Terminal 1 — backend**
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # fill in your Supabase values (optional for Day 1/2 — app boots without them)
uvicorn app.main:app --reload
```
Verify: open `http://localhost:8000/health` → `{"status": "healthy", "env": "development"}`.

**Terminal 2 — frontend**
```bash
cd frontend
npm install
cp .env.example .env             # defaults to http://localhost:8000, matches the backend above
npm run dev
```
Verify: open `http://localhost:5173` in a browser.
- You should see the "My Drive" sidebar layout with empty states.
- Top-right badge should read **"Backend connected (development)"** with a green dot within a couple seconds.
- If it reads "Backend unreachable" (red dot), confirm the backend terminal is still running on port 8000 and that `frontend/.env`'s `VITE_API_URL` matches it.

## Next up (Day 3)

File Upload & Object Storage: configure the Supabase Storage bucket for real, implement
the init-upload / signed-URL / complete-upload flow on the backend, save file metadata
in the DB. Not started yet — waiting on your confirmation of Day 2.
