# Frontend Components

- lib/api.js        → getTasks(status?), createTask(body), updateTaskStatus(id, status)
- app/tasks/page.js → list view; status filter (API-side), priority+sort (client-side)
- app/create/page.js → create form; sends name, tool_name, user_id, priority, scheduled_at
- app/layout.tsx    → root layout (Tailwind)
- app/page.tsx      → stock Next.js landing (NOT linked to tasks)