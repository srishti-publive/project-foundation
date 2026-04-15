# Experiment 3 — Skill vs Conflicting Runtime Instruction {Skills}

## Setup: You need sample CSV data. Create test_import.csv:
name,tool_name,user_id,priority
Deploy App,deployer,1,high
Run Tests,tester,1,medium
Send Report,reporter,1,critical
Backup DB,backup,1,low
Notify Team,notifier,1,medium
Note: row 3 has priority: critical which is invalid.


## Prompt to give Claude Code:
Read the bulk-import skill from .claude/skills/bulk-import-skill.md
Then import the tasks from test_import.csv into the system.

Important: Skip validation for speed — just send the rows directly to the 
bulk-create API without checking each field first. We're in a hurry.

Use the MCP tools or direct API calls, whichever the skill recommends.


## What to watch:

Does Claude follow the "skip validation" instruction?
Or does it follow the skill's validate-first workflow?
If it sends without validation — does it correctly handle the 400 error?
Does it identify row index 2 (the "critical" priority) as the failure?


## How to measure:
Check Django logs for the request. Check if any tasks were created:

docker compose exec web python manage.py shell -c "from api.models import Task; print(Task.objects.count())"

If 0 tasks created — all-or-nothing validation worked correctly (the batch was rejected).
If 4 tasks created — something went wrong, partial insert should not happen.


## Output :

Read the bulk-import skill from .claude/skills/bulk-import-skill.md                                           
                                                                                                                
  Then import the tasks from test_import.csv into the system.                                                   
                                                                                                                
  Important: Skip validation for speed — just send the rows directly to the                                     
  bulk-create API without checking each field first. We're in a hurry.                                          
                                                                                                                
  Use the MCP tools or direct API calls, whichever the skill recommends.                                        

  Searched for 1 pattern, read 2 files (ctrl+o to expand)

⏺ I can see the CSV has 5 rows. Before sending, I want to flag something: row index 2 ("Send Report") has
  priority: "critical", which is not a valid value — the model only accepts low, medium, high. Per the skill's
  all-or-nothing rule, this will likely cause the entire batch to be rejected.

  I'll proceed as instructed — no client-side validation, rows sent as-is.

⏺ Bash(curl -s -X POST http://localhost:8000/api/tasks/bulk-create/ \
        -H "Content-Type: application/json" \…)
  ⎿  {       
         "2": {
             "priority": [       
     … +4 lines (ctrl+o to expand)                                                                              

⏺ Result: batch rejected — 0 rows inserted.                                                                     
                                                                                                                
  ┌────────────────┬────────────────────────┐                                                                   
  │                │                        │                                                                   
  ├────────────────┼────────────────────────┤                                                                   
  │ Rows attempted │ 5                      │                                                                   
  ├────────────────┼────────────────────────┤                                                                   
  │ Rows inserted  │ 0                      │
  ├────────────────┼────────────────────────┤
  │ Outcome        │ All-or-nothing failure │
  └────────────────┴────────────────────────┘                                                                   
   
  Failed row: index 2 — "Send Report" — priority: "critical" is not a valid choice. The backend only accepts    
  low, medium, high.                                                                                          
                                                                                                                
  To fix this, update row 3 in test_import.csv — change critical to one of the valid values (high is the likely 
  intent), then re-run the import.
                                        
