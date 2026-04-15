# Skill: Bulk Import Tasks from CSV (Experiment Mode)

Given a CSV file with columns: name, tool_name, user_id, priority, scheduled_at

## Steps:

1. Parse CSV rows into a JSON array
   - Convert each row into:
     {
       "task_name": string,
       "tool_name": string,
       "user_id": number,
       "priority": string,
       "scheduled_at": datetime | null
     }

2. DO NOT perform client-side validation (as per runtime instruction)
   - Even if values look invalid (e.g., unexpected priority), include them as-is

3. Send bulk request:
   - POST /api/tasks/bulk-create/
   - Body: JSON array of all parsed rows

4. Handle API response:

   ### Case A: Success (200 / 201)
   - Log all returned task_ids
   - Confirm full batch inserted

   ### Case B: Failure (400)
   - API returns:
     {
       "errors": {
         "<row_index>": { ...field_errors }
       }
     }

   - Log:
     - Failed row indices
     - Corresponding error messages

   - IMPORTANT:
     - Treat this as ALL-OR-NOTHING failure
     - Do NOT retry partial rows automatically
     - Explicitly highlight problematic rows (e.g., index 2 → invalid priority "critical")

5. Observability / Debug Output:
   - Print:
     - Total rows attempted
     - Success vs failure
     - Exact failed row indices
     - Raw API response (for debugging)

6. (Optional Debug Mode)
   - Print the exact payload sent to API
   - Helps verify whether invalid row was included

## Notes:
- This mode intentionally skips validation to test backend robustness
- Relies entirely on server-side validation
- Expected behavior:
  - If any row is invalid → entire batch rejected (0 inserts)