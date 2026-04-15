# Publive MCP

![Python](https://img.shields.io/badge/python-3.11-blue)
![Django](https://img.shields.io/badge/Django-6.0.x-green)
![Next.js](https://img.shields.io/badge/Next.js-16.2.2-black)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791)

Monorepo with a **Django REST Framework** API on **PostgreSQL**, a **Next.js (App Router)** UI for **Task** records, and **Docker Compose** for API + database. In addition, there’s a small **MCP stdio server** (`mcp_server/server.py`) that exposes the task API as MCP tools (via HTTP calls to the Django API).

---

## 1. Project overview

**What it does:** The backend exposes JSON under `/api/` for creating tasks (single or bulk), listing them with optional `status` filter, patching `status`, and peeking at the **next runnable pending task** or **future-scheduled** pending tasks. Tasks support **priority** (low / medium / high) and optional **scheduled_at**; **started_at** and **completed_at** exist on the model but are **not** set by the status PATCH view (only `claim_task()` in `api/queue.py` sets `started_at` when used).

**Problem it solves:** Centralized persistence and HTTP workflows for named jobs (`tool_name`, `user_id`) with lifecycle `pending` → `running` → `completed` | `failed`, ordered dispatch for workers, and deferred execution via `scheduled_at`.

**Who it’s for:** Developers who want a small full-stack example or internal tool: PostgreSQL-backed tasks, a minimal UI, and endpoints shaped for an external worker process.

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
| Language (frontend) | TypeScript | tooling; **mixed** `.tsx` / `.js` under `app/` |
| Lint | ESLint | `^9`, `eslint-config-next` 16.2.2 |
| Containers | Docker Compose | `docker-compose.yml`, build context `.` |

**Migration note:** `api/migrations/0001_initial.py` was generated with **Django 5.2.12** (header); `config/settings.py` targets **Django 6.0** docs. Reconcile versions in your environment if you see migration or runtime warnings.

**MCP note:** `mcp_server/server.py` uses the Python `mcp` SDK + `httpx` (async). These dependencies are not listed in `requirements.txt` in this repo; install them separately if you want to run the MCP server.

---

## 3. Repository layout

```
publive_mcp/
├── .mcp.json                 # MCP server configs (see §16) — contains secrets in this repo, rotate/remove
├── .mcp.json.example         # Template MCP config
├── readme.md                 # This file
├── CLAUDE.md                 # Agent-oriented project notes (commands, architecture)
├── .gitignore                # .env, __pycache__, *.pyc, db.sqlite3
├── requirements.txt
├── manage.py
├── docker-compose.yml        # postgres + web (Django runserver)
├── dockerfile                # Python 3.11; CMD gunicorn (lowercase filename)
│
├── mcp_server/
│   └── server.py             # MCP stdio server for task API
│
├── .claude/                  # Claude Code project helpers (see §18)
│   ├── context/              # api-schema.md, db-schema.md (may lag code)
│   ├── commands/             # migrate.md, logs.md, test-api.md
│   └── prompts/              # add-endpoints.md
│
├── config/
│   ├── settings.py           # PostgreSQL, CORS, INSTALLED_APPS, env vars
│   ├── urls.py               # /admin/, /api/ → api.urls
│   ├── wsgi.py
│   └── asgi.py
│
├── api/
│   ├── models.py             # Task (priority, scheduling, status, timestamps)
│   ├── serializers.py      # TaskSerializer — all fields
│   ├── views.py              # CRUD-ish + bulk_create, next_task, scheduled_tasks
│   ├── urls.py # Routes under /api/
│   ├── queue.py              # get_next_task(), claim_task() (no HTTP route for claim)
│   ├── admin.py
│   ├── management/commands/
│   │   └── run-scheduled.py  # manage.py run_scheduled (dispatch due scheduled tasks)
│   ├── tests.py              # Empty placeholder
│   └── migrations/
│       ├── 0001_initial.py
│       ├── 0002_task_input_data_task_output_data_task_status.py
│       └── 0003_task_priority_scheduled_at_started_at_completed_at.py
│
├── frontend/
│   ├── package.json
│   ├── next.config.ts, tsconfig.json, eslint.config.mjs, postcss.config.mjs
│   ├── AGENTS.md, CLAUDE.md  # Next.js agent notes
│   ├── README.md             # create-next-app default
│   ├── app/
│   │   ├── layout.tsx, page.tsx   # Root: stock Next landing (Tailwind)
│   │   ├── globals.css       # Shared styles for /tasks, /create
│   │   ├── tasks/page.js     # List, status filter, priority filter, sort
│   │   └── create/page.js    # Create with priority + optional scheduled_at
│   ├── lib/api.js            # getTasks, createTask, updateTaskStatus
│   └── public/
│
└── Images/                   # Screenshots (API/UI)
```

---

## 4. Architecture

**Style:** Single Django project + app `api`, separate Next.js client (not microservices).

**Request flow:**

1. Browser loads `/tasks` or `/create` (or stock `/` from `app/page.tsx`).
2. Client `fetch` in `frontend/lib/api.js` → `http://localhost:8000/api/...`.
3. `config/urls.py` → `api/urls.py` → `@api_view` handlers in `api/views.py`.
4. `TaskSerializer` ↔ `Task`; PostgreSQL via `DATABASES` in `config/settings.py`.

**Patterns:** DRF function views, model serializer, ORM in views, **open CORS** (`CORS_ALLOW_ALL_ORIGINS = True`). **No** DRF authentication or permission classes on task endpoints.

**Queue logic:** `api/queue.py` centralizes “who runs next”: `get_next_task()` is used by `GET /api/tasks/next/`. `claim_task(task_id)` performs `SELECT FOR UPDATE` and moves **pending → running** with `started_at` set; it is **not** exposed as its own URL (workers today must rely on `PATCH .../status/` for transitions or you add a `/claim/` route).

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
| `started_at` | `DateTimeField` | optional; set by `claim_task()` when claiming |
| `completed_at` | `DateTimeField` | optional; **not** set by current views |

---

## 6. API reference

Base path: **`/api/`**. No authentication on these routes.

### `GET /api/tasks/`

- **Query:** optional `status` — one of `pending`, `running`, `completed`, `failed`.
- **Response:** `200` JSON array of tasks (all serializer fields).

### `POST /api/tasks/create/`

- **Body:** JSON; any subset of model fields accepted by `TaskSerializer` (defaults apply: e.g. `status` → `pending`, `priority` → `medium`).
- **Success:** `200` with serialized task (default DRF status for `Response(serializer.data)`).
- **Errors:** `400` with `serializer.errors`.

### `POST /api/tasks/bulk-create/`

- **Body:** JSON **array** of task objects (non-empty).
- **Behavior:** Validates **every** item first; **all-or-nothing** — any invalid item yields `400` with a map of index → errors. On success, `bulk_create` and return `201` with array of tasks.

### `GET /api/tasks/next/`

- **Response:** Next claimable pending task (same rules as `get_next_task()`), serialized JSON.
- **Empty queue:** `204 No Content` with body `{"detail": "No claimable tasks."}` (clients should treat **204** as empty; some HTTP clients ignore bodies on 204).

### `GET /api/tasks/scheduled/`

- **Response:** `200` JSON array of **pending** tasks with `scheduled_at` **strictly after** now, ordered by `scheduled_at` ascending.

### `PATCH /api/tasks/<task_id>/status/`

- **Body:** `{"status": "<pending|running|completed|failed>"}`.
- **Invalid status:** `400` `{"error": "Invalid status"}`.
- **Missing id:** `404`.
- **Success:** `200` serialized task. **Note:** This view only updates `status` (and `save()` full row); it does **not** maintain `started_at` / `completed_at`.

---

## 7. Frontend

- **Routes:** `/create` (client form), `/tasks` (client list). **`/`** is the default Next.js template (`app/page.tsx`) and is **not** linked to tasks.
- **`lib/api.js`:** `API_URL = "http://localhost:8000/api"` — `getTasks(status?)`, `createTask(body)`, `updateTaskStatus(id, status)`. No centralized error handling.
- **`/create`:** Sends `name`, `tool_name`, `user_id`, `priority`, and optional `scheduled_at` (ISO-like string from `datetime-local`; ensure timezone expectations match the API’s `USE_TZ = True` / UTC).
- **`/tasks`:** Status filter refetches from API (`?status=`). **Priority** filter and **sort** (by priority or `created_at`) are **client-side** on the current fetch. No pagination.
- **Styling:** Task/create pages use classes from `globals.css`. Tailwind is installed; root `page.tsx` uses Tailwind utilities. `.card.running` / `.card.completed` / `.card.failed` in `globals.css` are **not** applied — cards use `className="card"` only; status is shown via inner `.status.*` spans.

---

## 8. Worker integration notes

- **Peek next work:** `GET /api/tasks/next/` (does **not** claim or change status).
- **Atomic claim:** `claim_task(task_id)` in `api/queue.py` is ready for use but has **no** dedicated HTTP endpoint; add e.g. `POST /api/tasks/<id>/claim/` if external workers need DB-level locking without racing on PATCH.
- **Complete / fail:** Today, `PATCH /api/tasks/<id>/status/` is the simple path; consider setting `completed_at` in the view or a dedicated complete endpoint if you need accurate timestamps.

---

## 9. Scheduled dispatch (`run_scheduled`)

There is a Django management command at `api/management/commands/run-scheduled.py`:

- **What it does:** Finds tasks where `status='pending'` and `scheduled_at <= now()` and updates them to `status='running'` (bulk update). It does **not** set `started_at`.
- **Run (Compose):**

```bash
docker compose exec web python manage.py run_scheduled
```

If you want this to run periodically, you can trigger it from cron as described in `.claude/commands/run-scheduled.md`.

---

## 10. Prerequisites

- **Docker** + **Docker Compose**, or **Python 3.11+**, **PostgreSQL**, and **Node.js** (npm) for the frontend.

---

## 11. Environment variables

There is **no** committed `.env.example`. Required for `config/settings.py` and Compose (`env_file: .env`):

| Variable | Purpose |
|----------|---------|
| `DJANGO_SECRET_KEY` | Django secret |
| `DJANGO_DEBUG` | Boolean; default `False` if unset |
| `POSTGRES_DB` | Database name (also Postgres container) |
| `POSTGRES_USER` | DB user |
| `POSTGRES_PASSWORD` | DB password |
| `DB_HOST` | Host (e.g. `db` in Compose) |
| `DB_PORT` | Port |

Create `.env` at the repo root; do not commit secrets.

---

## 12. Installation and migrations

```bash
pip install -r requirements.txt
python manage.py migrate
```

Compose:

```bash
docker compose exec web python manage.py migrate
```

Frontend:

```bash
cd frontend && npm install
```

---

## 13. Running the project

**Compose (API + Postgres):**

```bash
docker compose up --build
```

API: `http://localhost:8000` (Compose overrides image CMD with `runserver 0.0.0.0:8000`).

**API locally (no Docker):** set env vars, `migrate`, `python manage.py runserver`.

**Frontend dev:**

```bash
cd frontend && npm run dev
```

→ `http://localhost:3000` — use `/tasks`, `/create`.

**Production frontend:** `npm run build` && `npm run start`.

**Image default:** `dockerfile` **CMD** is Gunicorn on `config.wsgi:application`; Compose uses `runserver` for development.

**Docker filename:** `dockerfile` is lowercase; some tools expect `Dockerfile` — rename or set `dockerfile:` under `build` in Compose if needed.

---

## 14. Quick API checks (curl)

```bash
curl http://localhost:8000/api/tasks/
curl -X POST http://localhost:8000/api/tasks/create/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","tool_name":"test_tool","user_id":1,"priority":"high"}'
curl http://localhost:8000/api/tasks/next/
curl http://localhost:8000/api/tasks/scheduled/
```

Compose logs:

```bash
docker compose logs web --tail=50
```

---

## 15. Authentication and security

- Task API views do **not** enforce login or tokens.
- `ALLOWED_HOSTS = []` — configure before any real deployment.
- CORS allows all origins. Treat as **trusted-network / dev** unless you harden.

---

## 16. MCP (Model Context Protocol)

This repo contains two different MCP-related configuration/implementation artifacts:

- **`mcp_server/server.py`**: a Python MCP stdio server named `"publive-tasks"` that exposes tools:
  - `list_tasks` (calls `GET /api/tasks/` with optional params)
  - `create_task` (calls `POST /api/tasks/create/`)
  - `next_task` (calls `GET /api/tasks/next/`)
  - `update_status` (calls `PATCH /api/tasks/<id>/status/`)

It talks to the backend at `API = "http://localhost:8000/api"` and expects the Django API to be running.

- **`.mcp.json` / `.mcp.json.example`**: example MCP client/server configuration (for common servers like postgres/filesystem/fetch/git/rest-api/postman).

**Important security note:** the committed `.mcp.json` in this repo currently contains what looks like a **real Postman API key**. Treat it as compromised: rotate it and remove secrets from version control.

---

## 17. Testing and CI

- **`api/tests.py`:** empty — no Django tests.
- **Frontend:** `npm run lint` only; no `test` script in `package.json`.
- **CI:** no `.github/workflows` (or similar) in-repo.

---

## 18. Claude Code / `.claude`

Project-level Claude Code material:

- **`CLAUDE.md` (root):** commands, architecture summary, queue/frontend behavior.
- **`.claude/context/`:** `api-schema.md`, `db-schema.md` — short references; they may be **older** than the live model (e.g. missing priority / scheduling fields) — **trust the code and this readme first**.
- **`.claude/context/domain-glossary.md`**: terminology used in this project (task/worker/claim/dispatch/queue/tool).
- **`.claude/context/queue-logic.md`** and **`.claude/context/frontend-components.md`**: quick pointers to where queue logic and UI pieces live.
- **`.claude/commands/`:** small how-tos (`migrate.md`, `logs.md`, `test-api.md`, `seed-tasks.md`, `run-scheduled.md`) and design notes for a future `claim` endpoint (`claim-task.md`).
- **`.claude/prompts/add-endpoints.md`:** checklist for adding endpoints (model → migration → serializer → view → urls → `lib/api.js`).
- **`.claude/prompts/file-ops.md`**: reminders for keeping context docs updated + export/backup snippets.
- **`.claude/skills/`:** `bulk-import-skill.md` and `task-worker-skill.md` (high-level workflows, not executable code).
- **`.claude/MCP-config.json`**: example MCP server definitions (fetch/filesystem/postgres) for local development.
- **`.claude/settings.local.json`**: local toggles (e.g. disables MCP servers defined in `.mcp.json`).

---

## 19. AI agents used in this project (what they do)

This repository includes **AI-agent configuration and playbooks** intended to help humans build and operate the system. These agents are **development-time helpers** (for coding, debugging, and operations) and are **not required at runtime** for the Django/Next.js app to function.

### Repo-provided agent(s)

- **Cursor / Claude Code agent (developer tooling)**:
  - **Where configured**: `CLAUDE.md` + `.claude/` (prompts, commands, skills, context).
  - **What it’s used for**:
    - Understanding architecture and conventions (what files own what).
    - Adding endpoints safely (model → migration → serializer → view → url → frontend API → curl test).
    - Debugging the task lifecycle and queue behavior.
    - Operational snippets (migrations, logs, seeding tasks, dispatching scheduled tasks).

### “Skills” (agent playbooks)

These are **instructions** for an agent (or a human) to follow:

- **`bulk-import-skill.md`**: How to import tasks from CSV by converting rows to JSON and calling `POST /api/tasks/bulk-create/`, handling per-row errors.
- **`task-worker-skill.md`**: How to implement a basic worker loop that polls `GET /api/tasks/next/` and then patches status to `completed`/`failed`.

### MCP-related “agents”

- **MCP stdio server (`mcp_server/server.py`)**:
  - Exposes the Django task API as MCP tools (`list_tasks`, `create_task`, `next_task`, `update_status`) by making HTTP requests to `http://localhost:8000/api`.
  - This is an **integration adapter** so an MCP-capable client/agent can interact with tasks.

- **MCP client/server config (`.mcp.json`, `.mcp.json.example`, `.claude/MCP-config.json`)**:
  - Defines which MCP servers a client can start (filesystem/fetch/postgres/rest-api/postman, etc.).
  - **Security**: do not commit API keys or DB URLs with passwords.

### What these agents did “in this project”

- They **document and automate developer workflows** (how to migrate, seed, debug queue flow, add endpoints).
- They provide **runbooks** for building a worker and for bulk importing tasks.
- They provide **MCP connectivity** so external AI agents/clients can call the task API through MCP tools.

If you want the app to be “agent-driven” at runtime (e.g. a worker that claims tasks atomically via a `/claim/` endpoint), that’s a next step in the codebase—not something the `.claude/` files do by themselves.

---

## 20. Deployment notes

- **Docker image:** installs `requirements.txt`, exposes `8000`, runs Gunicorn.
- **Compose file:** dev-oriented bind mount + `runserver`.

---

## 21. Known gaps / TODOs

- No `claim` HTTP route for `claim_task()`.
- `update_task_status` does not set `completed_at` / `started_at`.
- `GET /api/tasks/next/` returns `204` with a JSON body — uncommon; clients should key off status code.
- `.claude/context/*.md` may not list all current fields.
- Root **`readme.md`** vs **`README.md`:** on case-insensitive filesystems they are the same file; use one canonical name in docs.

---

## Screenshots

Under `Images/` (e.g. `get_tasks_localhost_8000.png`, `get_tasks_next.png`, `api_task_status.png`, `get_tasks_status.png`).
