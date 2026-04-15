# CLAUDE.md

This file guides Claude Code when working in this repository. Keep it up to date — if the code and this file disagree, trust the code.

## What This Project Is

**Publive MCP** is a full-stack task management system. The backend is Django 6 + Django REST Framework running on port 8000, the frontend is Next.js 16 on port 3000, and the database is PostgreSQL 15. Tasks move through a simple lifecycle: `pending → running → completed` or `failed`. Priority, scheduling, and status transitions are all first-class concepts in the data model.

## Getting Things Running

### The Easiest Path (Docker)

```bash
docker compose up --build           # Starts PostgreSQL + Django on port 8000
docker compose exec web python manage.py migrate
```

The Dockerfile is named `dockerfile` (lowercase) — some tooling expects `Dockerfile` with a capital D, so keep that in mind if anything complains.

Environment variables live in `.env`. Required keys: `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `DB_HOST`, `DB_PORT`, `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`.

### Running Locally Without Docker

**Backend:**
```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver          # Port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev                         # Port 3000
npm run build                       # Production build
npm run lint                        # ESLint
```

### Common Day-to-Day Commands

```bash
# Apply migrations
docker compose exec web python manage.py migrate

# Create new migrations after model changes
docker compose exec web python manage.py makemigrations

# Run backend tests (note: api/tests.py is empty — no tests exist yet)
docker compose exec web python manage.py test api

# Lint the frontend
cd frontend && npm run lint
```

## Architecture

### Backend (`api/`, `config/`)

The backend follows a straightforward DRF pattern. A few things worth knowing before you touch anything:

- **`api/models.py`** — One model: `Task`. Fields include `task_id`, `name`, `tool_name`, `user_id`, `input_data`, `output_data`, `status` (pending/running/completed/failed), `priority` (low/medium/high), `created_at`, `scheduled_at`, `started_at`, and `completed_at`.
- **`api/serializers.py`** — `TaskSerializer` is a ModelSerializer that exposes all fields.
- **`api/views.py`** — All views are function-based using the `@api_view` decorator. No authentication or permissions are enforced yet. All new views should follow the same pattern.
- **`api/queue.py`** — Owns all queue logic. Do not add queue logic to views — keep the separation clean. `get_next_task()` and `claim_task(task_id)` handle priority-based dispatch. `claim_task` uses `SELECT FOR UPDATE` for concurrency safety.
- **`config/settings.py`** — PostgreSQL configured via `django-environ`. `CORS_ALLOW_ALL_ORIGINS = True` (fine for dev, must be locked down before going to production). `ALLOWED_HOSTS = []`.

**API routes** (all mounted under `/api/`):

| Method | Path | What it does |
|--------|------|--------------|
| `GET` | `/api/tasks/` | List tasks; optional `?status=` filter |
| `POST` | `/api/tasks/create/` | Create a single task |
| `POST` | `/api/tasks/bulk-create/` | Create multiple tasks |
| `GET` | `/api/tasks/next/` | Get the highest-priority pending task ready to run |
| `GET` | `/api/tasks/scheduled/` | Get pending tasks with a future `scheduled_at` |
| `PATCH` | `/api/tasks/<id>/status/` | Update a task's status |

**Priority ordering:** high → medium → low (internally mapped to ranks 1 → 2 → 3 via `Case/When`). Ties are broken by `created_at` ascending — oldest task wins.

### Frontend (`frontend/`)

The frontend uses Next.js App Router. Two integrated routes exist: `/create` (task creation form) and `/tasks` (task list). The root `/` page is still the stock Next.js template — it's not connected to anything.

A few things to be aware of:

- **`frontend/lib/api.js`** — The only file that talks to the backend. Base URL is hardcoded to `http://localhost:8000/api`. It exports `getTasks`, `createTask`, and `updateTaskStatus`. There's no error handling yet. All new API calls belong here.
- **Styling** — Custom styles live in `frontend/app/globals.css` (~300 lines). Tailwind CSS v4 is installed but none of the component markup uses utility classes — everything uses named CSS classes. The `.card.running`, `.card.completed`, and `.card.failed` rules in globals.css are currently dead code because task cards never get a dynamic status class applied.
- **Filtering** — On `/tasks`, the status filter re-fetches from the API (`?status=` query param). Priority filtering and sorting happen client-side after the fetch. There's no pagination — every load fetches all tasks.

### How Data Flows

Frontend pages call helpers in `lib/api.js` → Django REST API → PostgreSQL. The queue endpoints (`/next/`, `/status/`) are built for an external worker that claims and processes tasks.

## Rules to Follow

- **All API views go in `api/views.py`** — use the `@api_view` decorator pattern consistently.
- **New models always get a migration before use** — run `makemigrations` and commit the migration file.
- **Queue logic stays in `api/queue.py`** — don't leak it into views.
- **`lib/api.js` is the only frontend file that calls the backend** — keep it that way.
- **Python:** snake_case, Django ORM only (no raw SQL).
- **TypeScript/JS:** camelCase, async/await for all API calls.
- **New endpoints:** follow the checklist in `.claude/prompts/add-endpoints.md`.

## Known Issues

These are real gaps in the current codebase — don't work around them silently, fix them properly when the time comes:

1. **`claim_task()` has no HTTP route.** It's called internally from the `next_task` view, but there's no dedicated `/api/tasks/<id>/claim/` endpoint. External workers can't atomically claim a task without adding one.
2. **`completed_at` and `started_at` are never set.** The `PATCH /status/` view doesn't update these timestamps when a task transitions state.
3. **`.claude/context/*.md` may be stale.** If anything in those files conflicts with this file or the actual code, trust the code.

## Claude Code Config (`.claude/`)

Project-level Claude Code configuration lives here:
- `settings.json` — project settings
- `agents/` — custom sub-agent definitions
- `hooks/` — event hook scripts (`.sh` files are chmod +x)
- `skills/` — reusable skill definitions