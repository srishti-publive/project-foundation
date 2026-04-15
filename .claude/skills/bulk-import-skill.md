# Skill: Bulk Import Tasks from CSV

Given a CSV file with columns: name, tool_name, user_id, priority, scheduled_at
1. Parse CSV rows into JSON array
2. POST /api/tasks/bulk-create/ with the array
3. Handle errors: API returns {index: errors} map on 400
4. Log successful task_ids