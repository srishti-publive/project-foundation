# Debug Task Flow

When a task is stuck or not transitioning:
1. Check current status: GET /api/tasks/?status=pending
2. Check next claimable: GET /api/tasks/next/
3. Check if scheduled_at is blocking: GET /api/tasks/scheduled/
4. Verify DB directly: docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB
   Then: SELECT task_id, name, status, priority, scheduled_at FROM api_task ORDER BY created_at DESC LIMIT 10;
5. If claim_task needed: look at api/queue.py — no HTTP route yet, add one if needed