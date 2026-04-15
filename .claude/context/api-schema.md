# API Schema Reference

## Endpoints

GET    /api/tasks/                    → list (filter: ?status=)
POST   /api/tasks/create/             → create one task
POST   /api/tasks/bulk-create/        → create many (all-or-nothing)
GET    /api/tasks/next/               → next claimable task (204 if empty)
GET    /api/tasks/scheduled/          → future-scheduled pending tasks
PATCH  /api/tasks/<id>/status/        → update status field only

Priorities: low | medium | high  (dispatch order: high first)
Statuses:   pending | running | completed | failed