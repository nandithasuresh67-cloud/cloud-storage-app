# Cloud Storage Service — MVP

Google Drive–style file storage & sharing app. Stack: **React + Vite + Tailwind**
(frontend, starts Day 8), **FastAPI** (backend), **Supabase Postgres** (database),
**Supabase Storage** (files). Built against the 14-day plan in the project spec.

## Day 12 status — Search, Sorting & Optimization ✅

- [x] **Search bar** — the header's search input (disabled since Day 2) is wired up: debounced (300ms), navigates to `/search?q=...`, backed by the real `GET /search` (Day 6 API). Results page has an All/Folders/Files filter, matching the backend's `item_type` param; clicking a folder navigates in, clicking a file opens the same preview modal used on My Drive.
- [x] **Sorting by name/date/size** — clickable column headers on My Drive (`SortableHeader`), toggling ascending/descending. This is **real server-side sorting**, not a client-side re-sort of an already-fetched page — see the note below on why that distinction actually matters here.
- [x] **Pagination / lazy loading** — a genuine "Load more" button backed by `useInfiniteQuery`, fetching 25 items at a time from the backend rather than the whole folder upfront.

**Why sorting and pagination needed a backend change, not just frontend work:** `GET /folders/contents` had no `sort_by`/`sort_order`/`limit`/`offset` before today — it returned every item, always ordered by name. Sorting purely client-side after fetching one page would only reorder whatever happened to already be loaded; as soon as a folder has more than one page, "sort by size" would silently produce a wrong answer (correct-looking on a small test folder, broken on a real one) instead of actually sorting the full set. So this day added real query params to the endpoint: `sort_by` (name/size/updated_at), `sort_order` (asc/desc), `limit`, `offset`, plus `subfolders_total`/`files_total` in the response so the frontend knows when to stop offering "Load more". Folders have no `size` column, so `sort_by=size` falls back to sorting folders by name rather than erroring or returning an undefined order.

**Tested, not assumed:**
- New pytest coverage for the pagination/sorting change specifically: default sort order, explicit ascending/descending on both name and size, the folder-has-no-size fallback, an invalid `sort_by` value correctly rejected with `422`, and — the one that actually matters — **walking every page with a small fixed limit reconstructs the exact original set with no duplicates and no gaps**. Pagination bugs almost always show up exactly there (an off-by-one, or ties in the sort column jumping between pages), so I didn't just check that *a* page loads correctly, I checked that paging through everything adds up. 93 backend tests total now (up from 89), all passing, plus all 4 smoke scripts.
- Clean `npm run build` and `oxlint` (0 warnings) on a fresh install.
- **Full real end-to-end test**: booted the real backend against a real local database, created 30 real folders, and replayed the exact HTTP calls `useFolderContents`'s pagination math and `SortableHeader`'s click-to-toggle logic issue — confirmed page 1 returns 25 items with `subfolders_total: 30` (so "Load more" correctly appears), page 2 returns the remaining 5 with zero overlap, sorting flips correctly in both directions, and files sort by actual byte size. Also replayed the search bar's exact debounced-navigation target and the results page's folder-only filter against real data.

**Scope note:** sorting and pagination were added to `GET /folders/contents` (My Drive) specifically, since that's the primary listing surface the spec's day title refers to. Search results are not paginated or sortable — reasonable for a search results list, which the spec doesn't call out as needing either.

## Day 11 status — Sharing UI & Permissions ✅

Sharing is now a real, working feature from the UI — not just an API.

- [x] **Share modal** — click the share icon that appears on hover over any file/folder row, or "Share this folder" when inside one. Lets you invite by email with a **viewer/editor permission selector**, shows the list of people who currently have access with a revoke button, and manages a public link (create, copy, revoke, with password-protection support already surfaced from the backend).
- [x] **Show shared users** — the modal's "Who has access" list, and a newly-wired **Shared with me** page (previously a Day 2 placeholder) showing everything actually shared with you, with your role, via the real `GET /shares/shared-with-me` endpoint (built Day 5).
- [x] **Public link landing page** (`/shared-link/:token`) — new, not previously planned as a standalone page, but necessary: a "Copy link" button that copies a URL to nowhere isn't a complete sharing UI. This is a genuinely public, unauthenticated page — handles the happy path, password prompt, wrong password, expired link, and revoked/bogus link states.
- [x] **One small backend addition**: `GET /public-link?file_id=` / `?folder_id=` — listing active links for a resource. This didn't exist before Day 11 (only create/revoke/access did), and without it the Share modal would have no way to know a link already exists when reopened, so a matching gap in the plan got closed rather than worked around. Covered by 4 new pytest tests (89 total now); owner-only, same pattern as the existing `GET /shares`.

**Tested, not assumed:**
- Clean `npm run build` and `oxlint` (0 warnings); confirmed all new files serve with no 404s, including SPA routing for the new public `/shared-link/:token` route.
- **Full real end-to-end test**: booted the real backend (local SQLite) and drove the *exact* HTTP sequence each frontend component issues, using two real registered users (an owner and someone shared with) — invite by email, list shares, promote/revoke, create a public link, access it with **no auth at all** (confirming the public path genuinely requires no login), password-protected link with wrong/missing/correct password, and permission boundaries (a viewer correctly gets `403` trying to list shares or create a link). Every response shape was checked against exactly what the React components destructure, not just "does it return 200."
- All 89 backend tests (85 + the 4 new listing-endpoint tests) and all 4 smoke-test scripts pass.

**Scope note:** the Share modal only surfaces one public link per resource even though the backend allows creating several (documented in the component) — reopening always shows/manages the same one rather than letting you juggle multiple links, which matches how most users would actually want this to work. Clicking a file shared directly with you (as opposed to a folder) from the "Shared with me" page doesn't open a preview yet — only folder navigation is wired there; noting this now rather than leaving it to be discovered as a dead click.

## Day 10 status — File Upload & Preview UI ✅

Upload is now a real, working feature — not a disabled button.

- [x] **Drag & drop upload** (`react-dropzone`) — drag files anywhere over the file
  list to upload them into the current folder; a dashed-border overlay confirms the
  drop target while dragging.
- [x] **Click-to-browse Upload button** — now enabled, opens the native file picker
  via the same `react-dropzone` instance (`noClick: true` + a manual `open()` call),
  so both interaction paths share one upload pipeline instead of two.
- [x] **Upload progress indicator** — `UploadProgressPanel`, fixed bottom-right,
  shows every in-flight upload independently (queued → uploading with a real
  percentage bar from axios's `onUploadProgress` → finishing → done/error). One
  file failing (oversized, blocked type) doesn't block or affect the others.
- [x] **File preview** — clicking any fully-uploaded file opens `FilePreviewModal`:
  inline `<img>` for images, an `<iframe>` for PDFs, and a clean "preview not
  available, here's Download instead" fallback for everything else. Files still
  mid-upload (`upload_status: "pending"`) are visually dimmed and explicitly can't
  be opened, rather than opening into a broken preview.
- [x] `useFileUpload` hook orchestrates the real 3-step flow per file: `POST
  /files/init-upload` → `PUT` the raw bytes straight to the signed URL (Day 3's
  design — bytes never pass through our backend) → `POST
  /files/{id}/complete-upload`. Backend validation errors (413 oversized, 415
  blocked type) surface as the exact per-file error message from the API, not a
  generic "upload failed."

**Tested for real, not assumed — this is the part worth reading closely:** this
sandbox can't reach Supabase and has no headless browser, so neither "just trust the
Supabase docs" nor "click through it in a real browser" were options. Instead: stood
up a tiny local fake object-storage server, temporarily pointed the backend's
storage layer at it (restored from git immediately after, `git diff` confirmed
clean), and replayed the **exact HTTP sequence `useFileUpload.js` issues** with
`curl` — `init-upload` → `PUT` real file bytes → `complete-upload` → `GET` the file
→ fetch its `download_url` → **byte-for-byte diff against the original file**. Did
this for both a text file and a real PNG image, confirming the upload round-trip is
byte-perfect and that `<img src={download_url}>` will render the exact bytes that
were uploaded. Also confirmed the 413/415 error responses match the exact shape the
upload hook reads (`err.response.data.detail`). Separately: clean `npm run build`,
clean `oxlint`, all new files served correctly by the dev server, and all 81 backend
tests still pass against the real (restored) storage code.

## Day 9 status — Dashboard & File Listing UI ✅

My Drive is now a real, working file browser instead of a static empty state.

- [x] **File & folder listing** — `pages/Dashboard.jsx` calls the real `GET /folders/contents` (built Day 4) via a new `useFolderContents` React Query hook. Subfolders and files render in a table with name, size, and last-modified date; files get a mime-type-aware icon (`FileTypeIcon`), folders are clickable to navigate in.
- [x] **Breadcrumb navigation** — `Breadcrumb` was rebuilt to accept clickable `{label, to}` items instead of plain strings, fed by the real breadcrumb array the backend already computed (Day 4). Clicking any ancestor navigates straight there; nested folders use a new `/folder/:folderId` route, `/` renders the root.
- [x] **New Folder** — a real, working button and modal (`NewFolderModal`), calling `POST /folders` (Day 4) via a `useCreateFolder` mutation, so the dashboard isn't just displaying pre-seeded data — you can actually build out a folder tree from the UI.
- [x] Sidebar's "My Drive" link now correctly highlights active when viewing any nested folder, not just the exact root path.
- [x] Loading state (spinner), error state (e.g. a deleted or no-longer-shared folder returns a real backend error message, not a generic failure), and empty state are all handled distinctly.

**Scope note:** per the spec, Day 9 is listing + navigation only — Upload stays disabled (real button, clear tooltip) since drag-and-drop upload is explicitly Day 10. This does mean you can create and navigate folders end-to-end right now, but can't yet get a file to actually appear via the UI (the backend upload API has worked since Day 3 — see the Postman collection — there's just no UI button wired to it yet). **Shared / Starred / Trash pages are still the Day 2 static placeholders** — wiring those to their real backend data (Days 5 and 6) wasn't in Day 9's scope and hasn't happened yet; flagging this now so it isn't mistaken for missing/broken later. Let me know if you'd rather I pull Day 10's upload forward so you can test file listing with real files sooner, or continue day-by-day.

**Tested, not assumed:**
- Clean `npm run build` and `oxlint` (0 warnings) after the changes, and confirmed every new/changed file (`Dashboard.jsx`, `NewFolderModal.jsx`, `FileTypeIcon.jsx`, `Breadcrumb.jsx`, `Sidebar.jsx`, `useFolderContents.js`, `services/folders.js`, `utils/format.js`) serves with no 404s from the dev server.
- **Full real end-to-end test**, not just a build check: booted the real backend (local SQLite) and real Vite dev server together, then drove the actual flow with `curl` using real `Origin`/cookie headers exactly as a browser would — registered, created a root folder, created a nested folder inside it, and confirmed `GET /folders/contents` returns exactly the shape `Dashboard.jsx` and `Breadcrumb.jsx` destructure (`folder`, `breadcrumb`, `subfolders`, `files`) at both the root and nested level.
- Confirmed a `pending` (incomplete) upload renders its "upload incomplete" badge correctly, and that a 404 from a deleted/inaccessible folder returns a `detail` message in the exact shape the Dashboard's error state reads.
- All 81 backend tests and all 4 smoke-test scripts still pass — nothing on the backend changed today, verified rather than assumed.

## Day 8 status — Frontend Setup & Auth UI ✅ (also: real backend auth finally built)

This day did double duty. The spec's Day 8 assumes backend auth already exists —
it was supposed to land on the original "Day 2" backend slot, before this project's
day-by-day requests reordered the frontend ahead of it. That gap has been called out
in every day's README section since (`X-User-Id` header, no real login). It gets
closed here, since Day 8's frontend work has nothing real to integrate with otherwise.

**Backend — real JWT auth, replacing the temporary header:**
- `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout`, `GET /auth/me`
- **HttpOnly cookies**, not a token in the response body — JavaScript can never read
  them, so an XSS bug in the frontend can't just read a token out of `localStorage`
  and exfiltrate it. Access token cookie is scoped `path=/`; refresh token cookie is
  scoped `path=/auth/refresh` only, so it isn't sent on every ordinary request.
- Same error message for "no such email" and "wrong password" on login — doesn't let
  an attacker enumerate which emails have accounts.
- Passwords never appear in any response body (checked explicitly in tests, not just assumed).
- The old `X-User-Id` header still works, **but only when `ENV != "production"`** —
  kept so the 66 existing Day 3–7 tests and the Postman collection didn't need
  rewriting, but hard-blocked (not just discouraged) outside development. Verified
  directly: flipping `ENV` to `"production"` mid-test causes the header to be
  rejected with `401`, not silently ignored.

**Frontend — Login & Signup pages:**
- `pages/Login.jsx`, `pages/Signup.jsx` — plain email/password forms, no
  token-handling code needed at all on the frontend, since cookies are set and sent
  automatically by the browser once `api.js`'s `withCredentials: true` (already set
  back on Day 2) is in place.
- `ProtectedRoute` — redirects to `/login` if `GET /auth/me` fails; `GuestRoute` —
  redirects logged-in users away from `/login`/`/signup` back to the dashboard.
- `UserMenu` in the header — shows the logged-in user's name/email and a working
  logout button.

**Tested, not assumed — including a real bug found along the way:**
- 15 new pytest tests (`tests/test_auth.py`): register/login/logout/refresh,
  wrong-password and duplicate-email rejection, `/auth/me` requiring auth, a
  protected endpoint (`POST /folders`) actually working off the session cookie (not
  just `/auth/me`), two independent login sessions not leaking into each other, and
  the production lockout of the dev header fallback.
- While converting, found that JWT `iat` has only 1-second resolution — a
  register-then-immediately-refresh within the same test produced byte-identical
  tokens, making "rotation" undetectable. Fixed by adding a random `jti` claim to
  every token, not just noted and left as a quirk.
- **Full real end-to-end test**, not just the mocked pytest client: booted the real
  backend against a real local SQLite database and the real Vite dev server
  together, then drove the actual HTTP flow with `curl` using real `Origin` headers
  and a real cookie jar — CORS preflight, register, `/auth/me`, and creating a real
  folder off the session cookie all confirmed working exactly as a browser would do it.
- Frontend: clean `npm run build`, clean `oxlint`, and confirmed every new file
  (`Login.jsx`, `Signup.jsx`, `useAuth.js`, `auth.js`, `UserMenu.jsx`, etc.) is served
  correctly by the dev server with no 404s.
- All 81 backend tests (66 existing + 15 new) and all 4 manual smoke-test scripts
  still pass — the auth rework caused zero regressions.

## Day 7 status — Testing & Backend Deployment ⚠️ (mostly complete — deployment itself not executed)

- [x] **Automated unit tests (pytest)** — `backend/tests/` — 66 tests across 4 files, using proper pytest fixtures (fresh in-memory DB per test, mocked Supabase Storage) instead of the sequential manual scripts from Days 3–6. Run with `pytest` from `backend/`.
- [x] **API testing via Postman** — `backend/postman_collection.json` (generated from the live OpenAPI spec, one request per endpoint with example bodies) + `backend/postman_environment.json` (sets `baseUrl` and the temporary `X-User-Id` auth header as variables). Regenerate anytime with `python3 scripts/export_postman_collection.py` after adding new endpoints.
- [x] **Environment variable setup** — `backend/app/core/startup_checks.py` actively validates config at boot: in development it just logs warnings for anything missing; in `ENV=production` it **refuses to start** (exit code 1) if `JWT_SECRET_KEY` is still the default, or if Supabase/database credentials are missing. This is a real fail-fast check, not just a documented list of variable names.
- [x] **Deployment artifacts prepared**: `backend/Dockerfile` (verified: dependencies actually install cleanly in a fresh venv; confirmed `psycopg2-binary` needs no extra system packages by testing the import directly rather than assuming), `render.yaml` (Render Blueprint), `fly.toml` (Fly.io alternative) — both read `$PORT` correctly for their respective platforms.
- [ ] **Actual live deployment** — **not done**. I don't have Render/Fly.io accounts, and this sandbox's network egress doesn't reach either platform's API even if I did (see the Network Configuration notice — only pypi/npm/github-style domains are reachable here). What's here is everything needed to deploy in one pass yourself; see "Deploying the backend" below for exact steps. I could not build or run the Docker image either (no `docker` binary in this sandbox) — I verified its dependency-install logic against the real venv instead, which is the closest verification available here.

## Day 6 status — Search, Trash & Optimization ✅

- [x] **Search API**: `GET /search?q=<name>&item_type=file|folder&mime_type=<prefix>` — case-insensitive name substring match, optionally narrowed to files-only/folders-only and by mime-type prefix (e.g. `image/`). Scoped to items you own plus items directly shared with you; excludes trash.
- [x] **Trash**: `GET /trash` (lists only the *roots* of what you trashed — not each cascaded child separately), `POST /trash/{files,folders}/{id}/restore`, `DELETE /trash/{files,folders}/{id}` (permanent — requires the item to already be in the trash first, as a deliberate second step)
- [x] **Cascading soft delete for folders** — trashing a folder now recurses into every subfolder and file underneath it (this was flagged as a known gap back on Day 4; closed here). Restore and permanent delete cascade the same way, including actually removing each file's object from Supabase Storage during permanent delete.
- [x] **DB indexes for performance** — composite indexes on `(owner_id, folder_id, is_trashed)` and `(owner_id, is_trashed)` for files and folders (covers folder-contents listing and trash listing, the two most frequent query shapes), plus expression indexes on `lower(name)` for case-insensitive search without a full table scan, plus an index on `files.mime_type` for the type filter.

⚠️ **Two scoping limitations, both flagged rather than silently glossed over:**
- Restoring a folder restores *all* of its descendants, even ones that were individually trashed before the folder itself was. Tracking that precisely would need per-item "trash batch" bookkeeping beyond what a Day 6 MVP needs.
- Search only covers items you own or that were *directly* shared with you — it does not recurse into the contents of folders you have cascading access to via a parent share. Once you open such a folder (`GET /folders/contents`), the usual cascading permission check takes over as normal; search itself just doesn't walk every shared subtree on every keystroke.

## Day 5 status — Sharing & Permissions ✅

- [x] Role-based access control: **Owner** (full control), **Editor** (upload/rename/move/delete), **Viewer** (read-only), **Public User** (access via link) — implemented as a ranked enum in `app/services/permissions.py`
- [x] `POST /shares` — share a file/folder with another user by email + role. Owner-only. Sharing the same person again updates their role instead of creating a duplicate.
- [x] `GET /shares?file_id=` or `?folder_id=` — list who a resource is shared with (owner-only, "manage access")
- [x] `DELETE /shares/{id}` — revoke access
- [x] `GET /shares/shared-with-me` — top-level items shared with you
- [x] `POST /public-link` / `DELETE /public-link/{id}` — create/revoke a public link, optional expiry and password (owner-only)
- [x] `POST /public-link/{token}/access` — **no authentication required** — the "Public User" path from the spec's role list. Password sent in the body (not a query string) so it doesn't end up in server/proxy logs.
- [x] **Permission validation middleware** — every file/folder route (Day 3 & 4) was refactored from strict-ownership checks to `require_file_access(...)` / `require_folder_access(...)`, so shared access is enforced in one place instead of being bolted onto each route separately
- [x] **Sharing a folder cascades** to everything inside it — share the folder once, and viewer/editor access applies to every file and subfolder underneath, resolved by walking up each item's `parent_id` chain. Sharing a single file only grants access to that file.
- [x] Existence isn't leaked: no access at all → `404`; some access but not enough (e.g. viewer trying to `DELETE`) → `403`

⚠️ **Public folder links are one level deep.** A public link to a folder lists that folder's immediate files/subfolders, but browsing *into* a listed subfolder via the public link isn't wired up yet — that would need per-subfolder access derived from the same token. Noted as a known limitation rather than silently half-working.

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

Two terminals — backend first, then frontend. **As of Day 8, you need a real
database** — auth (register/login) writes to the `users` table, so unlike Days 1–2
the backend can boot without one but nothing useful works until it's connected.

**Terminal 1 — backend**
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # fill in your Supabase values (or point DATABASE_URL at local Postgres/SQLite for a quick try)
uvicorn app.main:app --reload
```
Verify: open `http://localhost:8000/health` → `{"status": "healthy", "env": "development"}`.

**Don't have Supabase set up yet?** For a quick local try without any of that, point
`DATABASE_URL` at a local SQLite file instead (this is exactly what I used to verify
Day 8 end-to-end):
```bash
# instead of the Supabase DATABASE_URL in .env, use:
echo 'DATABASE_URL=sqlite:///./dev.db' >> .env
echo 'JWT_SECRET_KEY=some-random-dev-string' >> .env
python3 -c "
from sqlalchemy import create_engine
from app.core.database import Base
from app.models.user import User
from app.models.folder import Folder
from app.models.file import File
from app.models.share import Share
from app.models.link_share import LinkShare
engine = create_engine('sqlite:///./dev.db')
Base.metadata.create_all(engine, tables=[User.__table__, Folder.__table__, File.__table__, Share.__table__, LinkShare.__table__])
print('tables created')
"
```
File upload/storage endpoints will still 502 without real Supabase Storage credentials,
but auth, folders, sharing, search, and trash all work fully against SQLite.

**Terminal 2 — frontend**
```bash
cd frontend
npm install
cp .env.example .env             # defaults to http://localhost:8000, matches the backend above
npm run dev
```
Verify: open `http://localhost:5173` in a browser.
- You should be redirected to **`/login`** automatically now (this is new as of Day 8 — the app requires auth).
- Top-right of the login page should show the app name; the connection badge lives inside the app shell, so you won't see it until after logging in.

## Trying the login flow (Day 8)

1. On `/login`, click **"Sign up"**.
2. Fill in email + a password (8+ characters) → **Sign up**.
3. You should land on the dashboard (`/`), with a colored circle top-right showing
   your initials — click it to see your email and a **Log out** button.
4. Click **Log out** → you should be sent back to `/login`.
5. Log back in with the same email/password → back on the dashboard again.
6. Try visiting `http://localhost:5173/` directly while logged out (e.g. after
   logging out, or in a fresh incognito window) — you should be redirected to
   `/login` automatically, not shown a broken or empty dashboard.

If step 2 fails with a network error rather than a validation message, the most
likely cause is `DATABASE_URL` not being set/reachable — check the backend
terminal's logs.

## Running the automated test suite (Day 7 & 8)

```bash
cd backend && source .venv/bin/activate
pip install -r requirements-dev.txt   # adds pytest on top of requirements.txt
pytest                                 # 81 tests, ~5-7 seconds, no network/Supabase needed
pytest -v                              # same, with each test name printed
```
Every test uses a fresh in-memory database and a mocked Supabase Storage client (see
`backend/tests/conftest.py`), so this never touches your real `.env` or Supabase project
— safe to run anytime, including in CI.

## Testing the API with Postman

1. Open Postman → **Import** → select `backend/postman_collection.json` and
   `backend/postman_environment.json`.
2. Select the **"Cloud Storage - Local"** environment (top-right dropdown).
3. Start the backend (`uvicorn app.main:app --reload`), then create a user row (see
   "Setting up Supabase" step 5 above, or use the one-liner in the Day 5 verification
   section below) and paste its id into the environment's `userId` variable — real
   auth isn't built yet, so every request authenticates via the temporary `X-User-Id`
   header (see `app/core/deps.py`).
4. Run any request. To regenerate the collection after adding new endpoints:
   ```bash
   cd backend && source .venv/bin/activate
   npm install -g openapi-to-postmanv2   # one-time
   uvicorn app.main:app --reload &        # needs to be running
   python3 scripts/export_postman_collection.py
   ```

## Deploying the backend

Two deployment configs are included — pick one. **I have not actually deployed
either of these** (no hosting accounts, and this sandbox's network egress doesn't
reach Render's or Fly.io's APIs regardless — see the Network Configuration notice).
What's here is everything needed to deploy in one pass; the steps below are exact,
not a sketch.

**Option A — Render** (`render.yaml` at the repo root):
1. Push this repo to GitHub.
2. Render dashboard → New → **Blueprint** → connect the repo. Render reads
   `render.yaml` automatically and creates the service.
3. Fill in the secrets Render will prompt for (marked `sync: false` in `render.yaml`):
   `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `DATABASE_URL`.
   `JWT_SECRET_KEY` is auto-generated by Render; `CORS_ORIGINS` defaults to a
   placeholder you should replace with your real frontend URL once it's deployed
   (Day 8+).
4. Deploy. Render builds `backend/Dockerfile` and health-checks `/health`.
5. **Before this is actually usable**: run the table-creation one-liner from
   "Setting up Supabase" step 5 above, pointed at your production `DATABASE_URL`
   (Alembic migrations don't exist yet — this is the same manual step as local dev).

**Option B — Fly.io** (`fly.toml` at the repo root):
```bash
# one-time
curl -L https://fly.io/install.sh | sh
fly auth login

fly launch --config fly.toml --no-deploy   # reads fly.toml, skips auto-deploy so secrets can be set first
fly secrets set \
  SUPABASE_URL=https://YOUR_PROJECT.supabase.co \
  SUPABASE_ANON_KEY=... \
  SUPABASE_SERVICE_ROLE_KEY=... \
  DATABASE_URL=postgresql+psycopg2://... \
  JWT_SECRET_KEY=$(openssl rand -hex 32) \
  CORS_ORIGINS='["https://your-frontend-domain"]'
fly deploy
```
Then run the same table-creation one-liner against production `DATABASE_URL` before
expecting real traffic to work.

**Either way**, confirm it's live with:
```bash
curl https://your-app.onrender.com/health     # or your Fly.io URL
# -> {"status": "healthy", "env": "production"}
```
If it instead fails to boot at all, check the platform's logs first — `app/core/startup_checks.py`
will refuse to start (and say exactly why) if `JWT_SECRET_KEY`, Supabase credentials, or
`DATABASE_URL` are missing in production, rather than booting into a broken state silently.

## Verifying the Day 3, 4, 5 & 6 flows (manual scenario scripts)

These predate the Day 7 pytest suite above and are kept because they're useful for a
human to read through one continuous scenario end-to-end, rather than dozens of
independent test functions.

**Without Supabase configured** — run the automated smoke tests, which fake the two
Supabase Storage calls where needed and check the real route/model code:
```bash
cd backend && source .venv/bin/activate
python3 scripts/dev_smoke_test.py         # Day 3: upload flow — 14 checks
python3 scripts/dev_smoke_test_day4.py    # Day 4: folders & file ops — 33 checks
python3 scripts/dev_smoke_test_day5.py    # Day 5: sharing & permissions — 40 checks
python3 scripts/dev_smoke_test_day6.py    # Day 6: search & trash — 33 checks
```
All four should end with `All checks passed.`

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

## Next up

The 14-day implementation is now complete. Day 13 covers the Trash UI, restore/permanent delete flows, and final regression checks. Day 14 covers deployment preparation, responsive polish, error handling, and final documentation.

## Day 13 status — Trash, Versioning & Final Testing ✅

- [x] **Trash UI** — the Trash page now uses the real `GET /trash` endpoint and shows deleted root items with name, type, and deleted time.
- [x] **Restore** — files and folders can be restored from Trash using the existing backend cascade behavior for folders.
- [x] **Permanent delete** — destructive deletion is behind a confirmation dialog and calls the real `/trash/{files,folders}/{id}` endpoint; storage cleanup remains handled by the backend.
- [x] **Loading and error states** — Trash has loading indicators, retry handling, and visible API error messages.
- [x] **Frontend crash recovery** — an error boundary prevents an unexpected React render error from leaving the app on a blank screen.
- [x] **Responsive pass** — the main shell, header, and Trash table adapt to smaller screens; wide data tables scroll horizontally instead of breaking the layout.
- [x] **Final backend regression coverage** — the existing trash tests cover cascading delete/restore, permanent deletion, storage cleanup, and ownership boundaries; Day 12's 93-test suite remains the baseline.

**Version history note:** `file_versions` is present in the data model, but version-upload/history is a Phase 2 feature in the project specification and was not added to the MVP because the existing backend has no version-upload contract. The Day 13 plan labels the version-history UI as optional.

## Day 14 status — Deployment & Polish ✅

- [x] **Frontend deployment preparation** — Vercel SPA rewrite configuration added in `frontend/vercel.json` so React Router routes resolve correctly after a refresh.
- [x] **Environment configuration** — `VITE_API_URL` is documented for local and production environments; no backend URL is hardcoded into the production build.
- [x] **Mobile responsiveness** — shell/header spacing and content sizing were adjusted for smaller viewports, while data-heavy tables remain usable with horizontal scrolling.
- [x] **Error handling & loaders** — existing feature pages expose API errors and loading states, with the global ErrorBoundary covering unexpected render failures.
- [x] **Documentation** — this README records the completed feature scope, known limitations, test status, and deployment configuration.

### Deployment checklist

**Backend (Render/Fly.io/Railway):**
1. Set the production environment variables from `backend/.env.example`.
2. Set `CORS_ORIGINS` to the exact Vercel frontend origin.
3. Deploy the `backend/` service using the existing deployment configuration.
4. Verify `GET /health` returns `{"status":"healthy", ...}`.

**Frontend (Vercel):**
1. Import the repository into Vercel.
2. Set the project root to `frontend`.
3. Build command: `npm run build`.
4. Output directory: `dist`.
5. Add `VITE_API_URL` with the deployed backend URL.
6. Redeploy after changing environment variables.
7. Verify login, My Drive, upload, search, sharing, Trash restore, and permanent delete against the live backend.
