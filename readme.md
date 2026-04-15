# Publive MCP

![Python](https://img.shields.io/badge/python-3.11-blue)
![Django](https://img.shields.io/badge/Django-6.0.x-green)
![Next.js](https://img.shields.io/badge/Next.js-16.2.2-black)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791)

Monorepo with a **Django REST Framework** API on **PostgreSQL**, a **Next.js (App Router)** UI for **Task** records, and **Docker Compose** for API + database. A small **MCP stdio server** (`mcp_server/server.py`) exposes the task API as MCP tools via HTTP calls to the Django backend.

---

## 1. Project overview

**What it does:** The backend exposes JSON under `/api/` for creating tasks (single or bulk), listing them with an optional `status` filter, patching `status`, and peeking at the **next runnable pending task** or **future-scheduled** pending tasks. Tasks support **priority** (`low` / `medium` / `high`) and an optional `scheduled_at`; `started_at` and `completed_at` are set automatically by the `PATCH /status/` view when a task transitions to `running` or `completed`/`failed` respectively.

**Problem it solves:** Centralized persistence and HTTP workflows for named jobs (`tool_name`, `user_id`) with lifecycle `pending → running → completed | failed`, priority-based dispatch for workers, and deferred execution via `scheduled_at`.

**Who it's for:** Developers who want a small full-stack example or internal tool — PostgreSQL-backed tasks, a minimal UI, and endpoints shaped for an external worker process.

---

## 2. Tech stack

Values are taken from `requirements.txt`, `frontend/package.json`, `dockerfile`, `docker-compose.yml`, and `config/settings.py`. Python packages in `requirements.txt` are **not pinned**; `config/settings.py` was generated for **Django 6.0.3**.

| Layer | Technology | Version / note |
|--------|-------------|----------------|
| API image | Python | 3.11 (`dockerfile`) |
| Web framework | Django | 6.0.x (`config/settings.py`) |
| API | Django REST Framework | unpinned |
| WSGI (image default CMD) | Gunicorn | unpinned |
| DB driver | psycopg2-binary | unpinned |
| Config | django-environ | unpinned |
| CORS | django-cors-headers | unpinned |
| Database (Compose) | PostgreSQL | `postgres:15` |
| Frontend | Next.js | 16.2.2 |
| Frontend | React / react-dom | 19.2.4 |
| Styling | Tailwind CSS | `^4` with `@tailwindcss/postcss` |
| Language (frontend) | TypeScript | tooling only; **mixed** `.tsx` / `.js` under `app/` |
| Lint | ESLint | `^9`, `eslint-config-next` 16.2.2 |
| Containers | Docker Compose | `docker-compose.yml`, build context `.` |

**Migration note:** `api/migrations/0001_initial.py` was generated with **Django 5.2.12** (file header); `config/settings.py` targets **Django 6.0** docs. Reconcile versions in your environment if you see migration or runtime warnings.

**MCP note:** `mcp_server/server.py` uses the Python `mcp` SDK + `httpx` (async). These are **not** in `requirements.txt` — install them separately if you want to run the MCP server.

---

## 3. Repository layout

```
publive_mcp/
├── .mcp.json                 # MCP server configs (see §16) — contains secrets, rotate immediately
├── .mcp.json.example         # Template MCP config
├── README.md                 # This file
├── CLAUDE.md                 # Agent-oriented project notes (commands, architecture)
├── .gitignore                # .env, __pycache__, *.pyc, db.sqlite3
├── requirements.txt          # Unpinned Python dependencies
├── manage.py
├── seed.py                   # Utility to bulk-seed tasks — currently a no-op (see §21)
├── docker-compose.yml        # postgres:15 + web (Django runserver for dev)
├── dockerfile                # Python 3.11; CMD gunicorn (lowercase filename — see §13)
│
├── mcp_server/
│   └── server.py             # MCP stdio server exposing 4 task tools
│
├── .claude/                  # Claude Code project helpers (see §18)
│   ├── context/              # api-schema.md, db-schema.md (may lag code)
│   ├── commands/             # migrate.md, logs.md, test-api.md, seed-tasks.md, etc.
│   ├── prompts/              # add-endpoints.md, new-feature.md, debug-task-flow.md
│   ├── skills/               # bulk-import-skill.md, task-worker-skill.md
│   ├── MCP-config.json       # Example MCP server definitions
│   └── settings.local.json   # Local Claude toggles (disables MCP servers for dev)
│
├── config/
│   ├── settings.py           # PostgreSQL, CORS, INSTALLED_APPS, env vars
│   ├── urls.py               # /admin/, /api/ → api.urls
│   ├── wsgi.py
│   └── asgi.py
│
├── api/
│   ├── models.py             # Task model (11 fields — priority, scheduling, timestamps)
│   ├── serializers.py        # TaskSerializer — all fields
│   ├── views.py              # 6 function-based API views
│   ├── urls.py               # Routes under /api/
│   ├── queue.py              # get_next_task(), claim_task() — no HTTP route for claim
│   ├── admin.py              # Task registered in Django admin
│   ├── management/commands/
│   │   └── run-scheduled.py  # Dispatches due scheduled tasks — **unregistered** due to hyphen in filename (see §9, §21)
│   ├── tests.py              # Empty placeholder — no tests yet
│   └── migrations/
│       ├── 0001_initial.py
│       ├── 0002_task_input_data_task_output_data_task_status.py
│       └── 0003_task_priority_scheduled_at_started_at_completed_at.py
│
├── frontend/
│   ├── package.json
│   ├── next.config.ts, tsconfig.json, eslint.config.mjs, postcss.config.mjs
│   ├── CLAUDE.md             # Frontend agent notes
│   ├── README.md             # create-next-app default (not project docs)
│   ├── app/
│   │   ├── layout.tsx        # Root layout with Geist Sans/Mono fonts
│   │   ├── page.tsx          # Stock Next.js template — not linked to tasks
│   │   ├── globals.css       # Custom styles for /tasks and /create (~244 lines)
│   │   ├── tasks/page.js     # Task list: status filter, priority filter, sort, actions
│   │   └── create/page.js    # Task creation form: name, tool, priority, scheduled_at
│   ├── lib/api.js            # getTasks, createTask, updateTaskStatus
│   └── public/               # Icons and logos
│
└── Images/                   # Screenshots (API/UI)
```

---

## 4. Architecture

**Style:** Single Django project + `api` app, separate Next.js client (not microservices).

**Request flow:**

1. Browser loads `/tasks` or `/create` (stock `/` comes from `app/page.tsx`, not linked to tasks).
2. Client `fetch` calls in `frontend/lib/api.js` → `http://localhost:8000/api/...`.
3. `config/urls.py` → `api/urls.py` → `@api_view` handlers in `api/views.py`.
4. `TaskSerializer` ↔ `Task` model; PostgreSQL via `DATABASES` in `config/settings.py`.

**Patterns:** DRF function-based views, model serializer, ORM only (no raw SQL), **open CORS** (`CORS_ALLOW_ALL_ORIGINS = True`). **No** DRF authentication or permission classes on task endpoints.

**Queue logic:** `api/queue.py` centralizes dispatch. `get_next_task()` is used by `GET /api/tasks/next/`. `claim_task(task_id)` performs `SELECT FOR UPDATE` and transitions **pending → running** with `started_at` set — but has **no HTTP route** (see §8 and §21).

**Priority ordering (`get_next_task`):** high → medium → low (ranks 1–3 via `Case`/`When`); ties broken by `created_at` ascending. Only **pending** tasks with `scheduled_at` null or **≤ now** are eligible.

---

## 5. Backend: `Task` model

Defined in `api/models.py`:

| Field | Type | Notes |
|-------|------|--------|
| `task_id` | `AutoField` | Primary key |
| `name` | `CharField(200)` | |
| `tool_name` | `CharField(200)` | |
| `user_id` | `IntegerField` | Not a FK to `auth.User` |
| `input_data` | `TextField` | null/blank ok |
| `output_data` | `TextField` | null/blank ok |
| `status` | `CharField(20)` | `pending` \| `running` \| `completed` \| `failed`; default `pending` |
| `priority` | `CharField(10)` | `low` \| `medium` \| `high`; default `medium` |
| `created_at` | `DateTimeField` | `auto_now_add` |
| `scheduled_at` | `DateTimeField` | optional; future values excluded from `get_next_task` |
| `started_at` | `DateTimeField` | optional; set to `now()` by `PATCH /status/` when transitioning to `running`, and also by `claim_task()` |
| `completed_at` | `DateTimeField` | optional; set to `now()` by `PATCH /status/` when transitioning to `completed` or `failed` |

---

## 6. API reference

Base path: **`/api/`**. No authentication on these routes.

### `GET /api/tasks/`

- **Query:** optional `?status=` — one of `pending`, `running`, `completed`, `failed`.
- **Response:** `200` JSON array of tasks (all serializer fields).

### `POST /api/tasks/create/`

- **Body:** JSON; any subset of model fields accepted by `TaskSerializer` (defaults apply — e.g. `status` → `pending`, `priority` → `medium`).
- **Success:** `201 Created` with serialized task.
- **Errors:** `400 Bad Request` with `serializer.errors`.

### `POST /api/tasks/bulk-create/`

- **Body:** JSON **array** of task objects (non-empty).
- **Behavior:** Validates **every** item first; **all-or-nothing** — any invalid item yields `400` with a map of `index → errors`. On success, inserts via `bulk_create` and returns `201` with an array of tasks.

### `GET /api/tasks/next/`

- **Response:** `200 OK`. On success, the body is the serialized task. When the queue is empty, the body is `{"detail": "No claimable tasks.", "task": null}`.
- **Note:** This endpoint only *peeks* — it does **not** claim or change the task's status. Use `POST /api/tasks/<id>/claim/` to atomically claim it.

### `POST /api/tasks/<task_id>/claim/`

- **Purpose:** Atomically transition a task from `pending → running` using `SELECT FOR UPDATE`. Safe for concurrent workers — only one caller wins.
- **Body:** none.
- **Success:** `200` with the serialized task; `started_at` is set to `now()`.
- **Conflict:** `409` `{"error": "Task is not claimable (already claimed, completed, or missing)."}`.

### `GET /api/tasks/scheduled/`

- **Response:** `200` JSON array of **pending** tasks with `scheduled_at` **strictly after** now, ordered by `scheduled_at` ascending.

### `PATCH /api/tasks/<task_id>/status/`

- **Body:** `{"status": "<pending|running|completed|failed>"}`.
- **Invalid status:** `400` `{"error": "Invalid status"}`.
- **Not found:** `404`.
- **Success:** `200` serialized task.
- **Timestamps:** transitioning to `running` sets `started_at = now()`; transitioning to `completed` or `failed` sets `completed_at = now()`.

---

## 7. Frontend

- **Routes:** `/create` (task creation form), `/tasks` (task list). **`/`** is the default Next.js template (`app/page.tsx`) and is **not** linked to tasks.
- **`lib/api.js`:** `API_URL` is read from `process.env.NEXT_PUBLIC_API_URL` and falls back to `http://localhost:8000/api`. Exports `getTasks(status?)`, `createTask(body)`, `updateTaskStatus(id, status)`, `claimTask(id)`, `getNextTask()`, and `getScheduledTasks()`. All calls go through a shared `request()` wrapper that throws an `Error` (with `.status` and `.body`) on non-2xx responses and on network failures.
- **`/create`:** Sends `name`, `tool_name`, `user_id`, `priority`, and optional `scheduled_at` (ISO string from a `datetime-local` input; ensure timezone expectations match the API's `USE_TZ = True` / UTC setting).
- **`/tasks`:** Status filter triggers a fresh API fetch (`?status=`). Priority filter and sort (by priority or `created_at`) are **client-side** on the current result set. No pagination — every load fetches all tasks.
- **Styling:** Task and create pages use named classes from `globals.css`. Tailwind v4 is installed; the root `page.tsx` uses Tailwind utilities, but task/create pages exclusively use custom CSS classes. The `.card.running`, `.card.completed`, and `.card.failed` rules in `globals.css` are **dead code** — task cards only ever receive `className="card"`, never a status variant. Status is shown through inner `.status.*` span elements instead.

---

## 8. Worker integration notes

- **Peek next work:** `GET /api/tasks/next/` — does **not** claim or mutate the task.
- **Atomic claim:** `POST /api/tasks/<id>/claim/` → calls `claim_task()` which uses `SELECT FOR UPDATE` to safely transition `pending → running` and set `started_at`. Returns `409` if another worker already claimed the task. This is the endpoint concurrent workers should use.
- **Complete / fail:** Use `PATCH /api/tasks/<id>/status/`. The view sets `completed_at` automatically.

---

## 9. Scheduled dispatch (`run_scheduled`)

There is a Django management command at `api/management/commands/run-scheduled.py`:

- **What it does:** Finds tasks where `status='pending'` and `scheduled_at <= now()` and bulk-updates them to `status='running'` with `started_at=now()`.
- **Intended invocation:**

```bash
docker compose exec web python manage.py run_scheduled
```

> ⚠️ **Bug — command is currently unregistered.** The file is named `run-scheduled.py` with a **hyphen**, so `pkgutil.iter_modules` (used internally by Django's `find_commands`) skips it and Django never sees the command. `manage.py run_scheduled` (or any hyphenated variant) therefore fails with `Unknown command`. **Fix:** rename the file to `run_scheduled.py` (underscore). The class inside is already `Command`, so no other changes are needed.

For periodic dispatch, once the filename is fixed, trigger from cron as described in `.claude/commands/run-scheduled.md`.

---

## 10. Prerequisites

- **Docker** + **Docker Compose** — or **Python 3.11+**, **PostgreSQL**, and **Node.js** (npm) if running locally without containers.

---

## 11. Environment variables

Required for `config/settings.py` and Docker Compose (`env_file: .env`). There is no committed `.env.example` — create `.env` at the repo root and never commit it.

| Variable | Purpose |
|----------|---------|
| `DJANGO_SECRET_KEY` | Django secret key |
| `DJANGO_DEBUG` | Boolean; defaults to `False` if unset |
| `POSTGRES_DB` | Database name (also used by the Postgres container) |
| `POSTGRES_USER` | DB user |
| `POSTGRES_PASSWORD` | DB password |
| `DB_HOST` | Host — use `db` in Compose |
| `DB_PORT` | Port — typically `5432` |

---

## 12. Installation and migrations

**Backend (local):**
```bash
pip install -r requirements.txt
python manage.py migrate
```

**Backend (Compose):**
```bash
docker compose exec web python manage.py migrate
```

**Frontend:**
```bash
cd frontend && npm install
```

---

## 13. Running the project

**Compose (API + Postgres):**

```bash
docker compose up --build
```

API available at `http://localhost:8000` (Compose overrides the image CMD with `runserver 0.0.0.0:8000` for development).

**API locally (no Docker):** set env vars, run `migrate`, then `python manage.py runserver`.

**Frontend dev:**

```bash
cd frontend && npm run dev   # http://localhost:3000
```

Navigate to `/tasks` or `/create`. The root `/` is the stock Next.js template.

**Production frontend:**
```bash
npm run build && npm run start
```

**Image default:** `dockerfile` CMD is Gunicorn on `config.wsgi:application`; Compose uses `runserver` for development.

**Docker filename note:** the Dockerfile is named `dockerfile` (lowercase). Some tools expect `Dockerfile` with a capital D — rename it or set `dockerfile: dockerfile` explicitly under the `build` key in Compose if you encounter issues.

---

## 14. Quick API checks (curl)

```bash
# List all tasks
curl http://localhost:8000/api/tasks/

# Create a task
curl -X POST http://localhost:8000/api/tasks/create/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","tool_name":"test_tool","user_id":1,"priority":"high"}'

# Bulk create
curl -X POST http://localhost:8000/api/tasks/bulk-create/ \
  -H "Content-Type: application/json" \
  -d '[{"name":"Job A","tool_name":"tool_a","user_id":1},{"name":"Job B","tool_name":"tool_b","user_id":2}]'

# Peek at the next runnable task
curl http://localhost:8000/api/tasks/next/

# List scheduled (future) tasks
curl http://localhost:8000/api/tasks/scheduled/

# Update status (also sets started_at / completed_at automatically)
curl -X PATCH http://localhost:8000/api/tasks/1/status/ \
  -H "Content-Type: application/json" \
  -d '{"status":"running"}'
```

**Compose logs:**
```bash
docker compose logs web --tail=50
```

---

## 15. Authentication and security

- Task API views do **not** enforce login or tokens — all endpoints are open.
- `ALLOWED_HOSTS = []` — must be configured before any real deployment.
- `CORS_ALLOW_ALL_ORIGINS = True` — permissive; acceptable for dev, must be locked down for production.
- ⚠️ **The committed `.mcp.json` contains what appears to be a real Postman API key** — treat it as compromised, rotate it immediately, and remove secrets from version control.

---

## 16. MCP (Model Context Protocol)

**`mcp_server/server.py`** — a Python MCP stdio server named `"publive-tasks"` that exposes four tools:

- `list_tasks` — calls `GET /api/tasks/` with optional params
- `create_task` — calls `POST /api/tasks/create/`
- `next_task` — calls `GET /api/tasks/next/`
- `update_status` — calls `PATCH /api/tasks/<id>/status/`

It expects the Django API to be running at `http://localhost:8000/api`. The `mcp` and `httpx` packages it requires are **not** in `requirements.txt` — install them separately.

> ⚠️ **Bug — stale empty-queue detection.** The `next_task` handler still checks `r.status_code == 200` to decide whether there are tasks available. The backend was updated to return `200 OK` with `{"detail": "No claimable tasks.", "task": null}` when the queue is empty (see §6), so the MCP tool now forwards that sentinel body as if it were a real task. The handler should check for `body.get("task") is None` (or the presence of `detail`) before returning.

> ⚠️ **Bug — `list_tools` payload shape.** The handler returns plain dicts (`{"name": ..., "description": ...}`) with no `inputSchema`. Newer versions of the `mcp` SDK expect `Tool` objects with an `inputSchema`; older versions silently accept the dicts. If you upgrade the SDK and see validation errors, add `inputSchema` entries.

**`.mcp.json` / `.mcp.json.example`** — MCP client configuration files for common servers (postgres, filesystem, fetch, git, rest-api, postman). The committed `.mcp.json` currently contains a real API key (see §15).

---

## 17. Testing and CI

- **`api/tests.py`:** empty — no Django tests exist yet.
- **Frontend:** `npm run lint` only; there is no `test` script in `package.json`.
- **CI:** no `.github/workflows` or equivalent configured.

---

## 18. Claude Code / `.claude`

Project-level Claude Code configuration and reference material:

- **`CLAUDE.md` (root):** commands, architecture summary, queue/frontend behavior.
- **`.claude/context/`:** `api-schema.md`, `db-schema.md`, `domain-glossary.md`, `queue-logic.md`, `frontend-components.md` — short references. Some may be **older** than the live model (e.g. `db-schema.md` is missing the `priority`, `scheduled_at`, `started_at`, `completed_at` fields) — **trust the code and this README first**.
- **`.claude/commands/`:** operational how-tos (`migrate.md`, `logs.md`, `test-api.md`, `seed-tasks.md`, `run-scheduled.md`) and a design sketch for a future `claim` endpoint (`claim-task.md`).
- **`.claude/prompts/add-endpoints.md`:** checklist for adding new endpoints (model → migration → serializer → view → urls → `lib/api.js` → context docs → tests → curl).
- **`.claude/skills/`:** `bulk-import-skill.md` and `task-worker-skill.md` — high-level workflow playbooks.
- **`.claude/MCP-config.json`:** example MCP server definitions for local development.
- **`.claude/settings.local.json`:** local toggles (disables MCP servers defined in `.mcp.json`).

---

## 19. AI agents used in this project

This repository includes **AI-agent configuration and playbooks** to help humans build and operate the system. These are **development-time helpers** and are **not required at runtime** for the Django/Next.js app to function.

**Developer agent (Claude Code / Cursor):** configured via `CLAUDE.md` + `.claude/`. Used for understanding architecture, adding endpoints safely, debugging the task lifecycle and queue behavior, and running operational snippets (migrations, logs, seeding, scheduled dispatch).

**Agent skills (`.claude/skills/`):**

- `bulk-import-skill.md` — import tasks from CSV by converting rows to JSON and calling `POST /api/tasks/bulk-create/`, with per-row error handling.
- `task-worker-skill.md` — implement a polling worker loop that calls `GET /api/tasks/next/` and then patches status to `completed`/`failed`.

**MCP integration (`mcp_server/server.py`):** exposes the Django task API as MCP tools so any MCP-capable client or agent can interact with tasks. This is an integration adapter, not a background worker.

If you want agent-driven runtime behavior (e.g. a worker atomically claiming tasks via a `/claim/` endpoint), that is a next step in the codebase — the `.claude/` files provide the design sketch in `claim-task.md`.

---

## 20. Deployment notes

- Docker image installs `requirements.txt`, exposes port `8000`, and runs Gunicorn.
- Compose file is dev-oriented: bind mount for live code reload + `runserver` override.
- No `.dockerignore` — the bind mount copies everything (node_modules, `__pycache__`, etc.) into the container on build. Add a `.dockerignore` before any production image build.
- `requirements.txt` has no version pins — add pinned versions before deploying to prevent unexpected breakage on reinstall.

---

## 21. Bug fixes applied and remaining TODOs

### Bug fixes applied in this commit

- **`POST /api/tasks/create/` now returns `400` on validation error** (previously defaulted to `200`). It also now returns `201 Created` on success, matching REST conventions.
- **`run_scheduled` management command now sets `started_at`** in the same bulk update that flips `status` to `running`. Previously `started_at` was left `null` for scheduler-dispatched tasks.
- **Variable shadowing in `get_tasks` removed** — the local query-param variable was renamed from `status` to `status_filter` to stop shadowing `rest_framework.status`.
- **`GET /api/tasks/next/` now returns `200` with `{"detail": "...", "task": null}` when the queue is empty** instead of `204 No Content` with a JSON body (which many HTTP clients silently discard).
- **New endpoint `POST /api/tasks/<task_id>/claim/`** — exposes `claim_task()` over HTTP so external workers can claim tasks with row-level locking. Returns `200` on success, `409 Conflict` if the task is no longer claimable.
- **`update_task_status` no longer overwrites `started_at`** on repeat transitions into `running` — it only sets the timestamp if it is currently `null`, so re-entering `running` doesn't reset the clock.
- **Frontend `lib/api.js` rewritten**: API base URL is now read from `NEXT_PUBLIC_API_URL` (falls back to `http://localhost:8000/api`), all calls go through a shared `request()` helper that throws an `Error` (with `.status` and `.body`) on non-2xx or network failures, and new helpers `claimTask`, `getNextTask`, and `getScheduledTasks` are exported.

### Active bugs still in the tree

These are real defects that surface when you run the code as-is:

- 🐞 **`run-scheduled.py` is invisible to Django.** The file in `api/management/commands/` uses a hyphen in its name. Django's command discovery (`pkgutil.iter_modules`) skips any file whose stem is not a valid Python identifier, so `manage.py run_scheduled` / `manage.py run-scheduled` both fail with `Unknown command`. **Fix:** rename the file to `run_scheduled.py`.
- 🐞 **`seed.py` does nothing when run.** It defines `seed(tasks)` but has no `if __name__ == "__main__"` block, no list of sample tasks, and no call to `seed(...)`. Running `python seed.py` exits silently without seeding anything. It also imports `requests`, which is **not** in `requirements.txt`. **Fix:** add a sample `tasks = [...]` list, call `seed(tasks)` under an `__main__` guard, and add `requests` to `requirements.txt` (or rewrite it to use `django.test.Client` / Django ORM directly).
- 🐞 **MCP `next_task` no longer detects an empty queue.** `mcp_server/server.py` still relies on `r.status_code == 200` to decide "no tasks", but `GET /api/tasks/next/` now always returns `200` (with `{"task": null}` when empty). The MCP tool will therefore forward the sentinel body as a task. **Fix:** check `body.get("task") is None` or the presence of `detail`.
- 🐞 **MCP `list_tools` missing `inputSchema`.** See §16. Breaks under newer `mcp` SDK versions.
- 🐞 **`update_task_status` can re-stamp `completed_at` on retries.** If a task is flipped from `failed` back to `completed` (or vice versa), `completed_at = now()` is written again, clobbering the original timestamp. Analogous to the `started_at` guard that *was* added for `running`. Consider mirroring that guard: only set `completed_at` if it is currently `null`, or allow overwrite deliberately based on product rules.
- 🐞 **`CLAUDE.md` "Known Issues" section is stale.** It still lists "`claim_task()` has no HTTP route" and "`completed_at` / `started_at` are never set" — both have been fixed in the code. Update or remove those bullets.

### Remaining TODOs (not in scope for this fix)

- **No pagination on `/tasks`** — the frontend still loads all tasks in a single fetch. Add server-side pagination before the table grows.
- **Dead CSS** — `.card.running`, `.card.completed`, `.card.failed` rules in `globals.css` are never applied (cards only receive `className="card"`). Either apply a status class in the task list component or remove the unused rules.
- **`.claude/context/db-schema.md` is stale** — missing the `priority`, `scheduled_at`, `started_at`, and `completed_at` fields. Trust the code.
- **MCP server dependencies missing from `requirements.txt`** — `mcp` and `httpx` must be installed separately to run `mcp_server/server.py`.
- **Requirements are unpinned** — add explicit version constraints in `requirements.txt` before any production build.
- **Lowercase `dockerfile`** — rename to `Dockerfile` or set `dockerfile: dockerfile` explicitly in `docker-compose.yml` for tooling that is case-sensitive.
- **No tests** — `api/tests.py` is empty; there is no frontend test suite. Add unit tests for `api/queue.py` (priority ordering, scheduled filtering, atomic claim) and integration tests for the views.
- **Open CORS + empty `ALLOWED_HOSTS`** — lock both down before any real deployment. Note that with `DJANGO_DEBUG=False` and `ALLOWED_HOSTS = []`, Django will reject **every** request — the app is effectively unserveable in production until this is fixed.
- **Secret in `.mcp.json`** — rotate the committed Postman API key and move secrets to `.env`.
- **Missing `api/migrations/0001_initial.py` header vs. settings mismatch** — initial migration was generated on Django 5.2.12 while `config/settings.py` targets Django 6.0. Regenerate migrations against the target Django version if you hit compatibility warnings.
- **`api/Untitled`** — there is a stray `Untitled` entry under `api/` (visible in `ls`). Remove or rename if it isn't intentional.

---

## Screenshots

Under `Images/` — e.g. `get_tasks_localhost_8000.png`, `get_tasks_next.png`, `api_task_status.png`, `get_tasks_status.png`.
