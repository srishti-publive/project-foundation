# Skill: Task Worker

To process tasks from the queue:
1. Poll GET /api/tasks/next/ every N seconds
2. On 200: extract task_id, tool_name, input_data
3. Execute the tool (tool_name maps to a handler function)
4. On success: PATCH /api/tasks/<id>/status/ {"status": "completed"}
5. On error: PATCH /api/tasks/<id>/status/ {"status": "failed"}
6. On 204: wait and retry

Handler map (tool_name → function):
- "email_tool" → send_email(input_data)
- "pdf_tool"   → generate_pdf(input_data)
- "crm_sync"   → sync_crm(input_data)