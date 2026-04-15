# Domain Glossary

- Task       → A unit of work with a tool_name, user_id, priority, and lifecycle status
- Worker     → External process that polls /next/, claims, and executes tasks
- Claim      → Atomically take ownership of a pending task (sets running + started_at)
- Dispatch   → Move a scheduled task from pending to running when scheduled_at passes
- Queue      → The ordered set of pending tasks sorted by priority then created_at
- Tool       → The string identifier (tool_name) that maps to a worker handler function


Priority order (highest to lowest): high → medium → low
Status flow: pending → running → completed | failed
            (pending can also go → pending if re-queued, not currently implemented)