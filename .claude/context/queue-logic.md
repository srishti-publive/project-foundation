# Queue Logic

File: api/queue.py

get_next_task()  → ORM query, priority-ordered (high=1, medium=2, low=3),
                   ties broken by created_at ASC,
                   excludes scheduled_at > now()

claim_task(id)   → SELECT FOR UPDATE, sets status=running + started_at=now()
                   NOT exposed as HTTP endpoint yet (TODO)

Workers should:  GET /next/ to peek → POST /claim/ (TODO) to atomically take it