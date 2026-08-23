# Cloud Storage Service — MVP

Google Drive–style file storage & sharing app. Stack: **React + Vite + Tailwind**
(frontend, starts Day 8), **FastAPI** (backend), **Supabase Postgres** (database),
**Supabase Storage** (files). Built against the 14-day plan in the project spec.

## Day 4 status — Folder System & File Management APIs ✅

- [x] Folder CRUD: `POST /folders` (create, optionally nested via `parent_id`), `GET /folders/{id}`, `PATCH /folders/{id}` (rename and/or move), `DELETE /folders/{id}` (soft delete)
- [x] `GET /folders/contents?folder_id=<uuid>` (omit for root) — lists subfolders + files directly inside, plus the breadcrumb path to get there
- [x] File operations: `PATCH /files/{id}` (rename and/or move between folders), `DELETE /files/{id}` (soft delete)
- [x] Breadcrumb logic implemented by walking `parent_id` up to the root (`app/services/folder_service.py`)
- [x] Cycle prevention: moving a folder into itself or into one of its own descendants is rejected with `400`, instead of silently corrupting the tree
- [x] Ownership enforced everywhere (404, not 403, for folders/files you don't own — doesn't leak whether something exists)

⚠️ **Soft delete does not cascade yet.** Deleting a folder only flips that folder's own `is_trashed` — its children are untouched and still directly fetchable. Full recursive trash (and restore) semantics are a Day 6 feature; noted clearly in the route docstrings so it isn't mistaken for a bug.

No live-Supabase caveat this time — folders don't touch Storage at all, only the DB. Same testing approach as Day 3 (see below) still applies to the file init-upload calls this test also exercises.

## Day 3 status — File Upload & Object Storage ✅

- [x] File upload flow implemented: `POST /files/init-upload` → `POST /files/{id}/complete-upload` → `GET /files/{id}`
- [x] Client uploads bytes **directly to Supabase Storage** via a signed URL — file bytes never pass through the backend
- [x] File metadata (name, owner, folder, size, mime type, storage path, upload status) saved to the `files` table
- [x] Size validation (`MAX_UPLOAD_SIZE_MB`, default 100MB) and mime-type blocklist enforced on `init-upload`
- [x] `complete-upload` verifies the object actually exists in storage before marking a file "uploaded" — can't be faked by calling the endpoint without uploading
- [x] Ownership enforced: a file is only readable by the user who created it

⚠️ **Temporary auth stand-in** — real JWT auth (register/login/tokens) hasn't been built yet, since the frontend day got built ahead of it in this plan. Every endpoint that needs "the current user" currently reads a plain `X-User-Id: <uuid>` header instead of a verified JWT (see `app/core/deps.py` — it says so loudly in a docstring). **This is not secure** — anyone can claim to be any user by setting the header. It exists only so the upload flow could be built and tested against real foreign-key relationships today. This needs to be replaced with real auth before this goes anywhere near production; flagging it now so it isn't missed later.

⚠️ **Not tested against a live Supabase project** — this sandbox's network egress doesn't allow reaching `*.supabase.co`, so I could not verify the signed-URL flow against real Supabase Storage. What I did verify: an automated smoke test (`backend/scripts/dev_smoke_test.py`) boots the real FastAPI app against an in-memory database with the real model/route/validation code, and fakes out only the two Supabase network calls — proving the endpoint logic, size/type validation, ownership checks, and pending→uploaded status transition are all correct. The actual Supabase Storage calls (`create_signed_upload_url`, `list`, `create_signed_url`) are unit-tested against the installed `supabase-py` SDK's real method signatures, but not against a live bucket. **You'll need to test the real upload against your Supabase project yourself** once credentials are in `backend/.env` — see verification steps below.

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

## Setting up Supabase

1. Create a project at [supabase.com](https://supabase.com) (free tier is fine for MVP dev).
2. **Project Settings → API**: copy the `Project URL`, `anon public` key, and
   `service_role` key into `backend/.env` (`SUPABASE_URL`, `SUPABASE_ANON_KEY`,
   `SUPABASE_SERVICE_ROLE_KEY`).
3. **Project Settings → Database**: copy the connection string (use the *connection
   pooling* URI) into `DATABASE_URL` in `backend/.env`.
4. **Storage**: create a bucket named `files` (matches `SUPABASE_STORAGE_BUCKET` in
   `.env`). It can be **private** — the backend uses signed URLs for both upload and
   download, so the bucket never needs to be public.
5. **Database tables**: not created yet — Alembic migrations haven't been added, so for
   now you'll need to create the tables manually. Easiest option: temporarily run this
   once from a Python shell with your real `DATABASE_URL` set, to create every table
   from the SQLAlchemy models:
   ```bash
   cd backend && source .venv/bin/activate
   python3 -c "from app.core.database import Base, engine; import app.models; Base.metadata.create_all(engine)"
   ```
   (Alembic migrations will replace this ad-hoc step later.)

## Running everything locally

Two terminals — backend first, then frontend.

**Terminal 1 — backend**
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # fill in your Supabase values — required for Day 3 uploads to work
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

## Verifying the Day 3 & Day 4 flows

**Without Supabase configured** — run the automated smoke tests, which fake the two
Supabase Storage calls where needed and check the real route/model code:
```bash
cd backend && source .venv/bin/activate
python3 scripts/dev_smoke_test.py         # Day 3: upload flow — 14 checks
python3 scripts/dev_smoke_test_day4.py    # Day 4: folders & file ops — 33 checks
```
Both should end with `All checks passed.`

**Against your real Supabase project** — once `backend/.env` has real credentials and
the tables exist (see setup steps above), start the backend and run this from another
terminal. It uses a random `X-User-Id` — since real auth isn't built yet, you'll need
a matching row in the `users` table first, or you'll get a foreign-key error on
`init-upload`. Easiest way to get one:
```bash
python3 -c "
import uuid
from app.core.database import SessionLocal
from app.models.user import User
db = SessionLocal()
u = User(id=uuid.uuid4(), email='you@example.com', password_hash='x')
db.add(u); db.commit()
print(u.id)
"
```
Then, with that id as `USER_ID`:
```bash
# 1. init-upload — get a signed URL
curl -s -X POST http://localhost:8000/files/init-upload \
  -H "Content-Type: application/json" -H "X-User-Id: $USER_ID" \
  -d '{"filename":"test.txt","mime_type":"text/plain","size_bytes":11}'
# copy "upload_url" and "file_id" from the response

# 2. PUT the actual bytes straight to Supabase Storage
curl -s -X PUT "<upload_url from above>" \
  -H "Content-Type: text/plain" --data-binary "hello world"

# 3. complete-upload — backend verifies the object exists, marks it "uploaded"
curl -s -X POST http://localhost:8000/files/<file_id>/complete-upload \
  -H "X-User-Id: $USER_ID"

# 4. confirm metadata + a working signed download URL
curl -s http://localhost:8000/files/<file_id> -H "X-User-Id: $USER_ID"
```
Step 4's `download_url` should be a real, fetchable Supabase URL — opening it in a
browser should download the file you uploaded.

## Next up (Day 5)

Sharing & Permissions: role-based access control (owner/editor/viewer), share a
file/folder with another user, and public shareable links. Not started yet —
waiting on your confirmation of Day 4.
