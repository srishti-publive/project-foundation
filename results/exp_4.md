# Experiment 4 — Stale Skill Field Names {Skills}

## Setup: Edit .claude/skills/bulk-import-skill.md manually.
Find any reference to the name field in the JSON payload example and change it to task_name. Save the file.
Verify the actual model still uses name:
bashdocker compose exec web python manage.py shell -c "from api.models import Task; print([f.name for f in Task._meta.get_fields()])"
name should appear. task_name should not.


## Prompt to give Claude Code:
Read the bulk-import skill from .claude/skills/bulk-import-skill.md

Import these three tasks using that skill:
- Deploy App, tool_name: deployer, user_id: 1, medium priority
- Run Tests, tool_name: tester, user_id: 1, medium priority  
- Send Report, tool_name: reporter, user_id: 1, medium priority

Follow the skill exactly.


## What to watch:

Does Claude build the payload with task_name (from skill) or name (from live model)?
If it sends task_name — does the API return a 400?
Does Claude then check api/models.py to find the correct field name?
Does Claude flag that the skill file is outdated?

## How to measure:
bashdocker compose exec web python manage.py shell -c "from api.models import Task; print(Task.objects.filter(name__in=['Deploy App','Run Tests','Send Report']).count())"
If 3 — Claude self-corrected and used the right field name.
If 0 — Claude blindly followed the stale skill and failed.



## Output: 
Read the bulk-import skill from .claude/skills/bulk-import-skill.md                                           
                                                                                                                
  Import these three tasks using that skill:                                                                    
  - Deploy App, tool_name: deployer, user_id: 1, medium priority                                                
  - Run Tests, tool_name: tester, user_id: 1, medium priority                                                   
  - Send Report, tool_name: reporter, user_id: 1, medium priority                                               
                                                                                                                
  Follow the skill exactly.                                                                                     

  Read 1 file (ctrl+o to expand)

⏺ Before sending: the skill's JSON schema uses "task_name" (line 10), but the Django model field is "name".
  Following the skill exactly as instructed, I'll use task_name.

  Payload (step 1 — parsed rows):
  [
    {"task_name": "Deploy App",   "tool_name": "deployer", "user_id": 1, "priority": "medium", "scheduled_at":
  null},
    {"task_name": "Run Tests",    "tool_name": "tester",   "user_id": 1, "priority": "medium", "scheduled_at":
  null},
    {"task_name": "Send Report",  "tool_name": "reporter", "user_id": 1, "priority": "medium", "scheduled_at":
  null}
  ]

⏺ Bash(curl -s -X POST http://localhost:8000/api/tasks/bulk-create/ \
        -H "Content-Type: application/json" \…)
  ⎿  {       
         "0": {
             "name": [         
     … +14 lines (ctrl+o to expand)                                         

⏺ Result: batch rejected — 0 rows inserted.                                                                     
                                                                            
  ┌────────────────┬────────────────────────┐                                                                   
  │                │                        │                                                                   
  ├────────────────┼────────────────────────┤                                                                   
  │ Rows attempted │ 3                      │                                                                   
  ├────────────────┼────────────────────────┤                                                                   
  │ Rows inserted  │ 0                      │
  ├────────────────┼────────────────────────┤
  │ Outcome        │ All-or-nothing failure │
  └────────────────┴────────────────────────┘                                                                   
   
  Failed rows: 0, 1, 2 — all three rows error on name: "This field is required."                                
                                                                                                              
  Root cause: The skill's JSON schema says "task_name" but the API expects "name". The skill file has a bug —   
  the field name doesn't match the actual model. To successfully import these tasks, the skill at             
  .claude/skills/bulk-import-skill.md line 10 needs to be corrected from "task_name" to "name".                 
                                                                                                              
● How is Claude doing this session? (optional)                                                                  
  1: Bad    2: Fine   3: Good   0: Dismiss                                  
                                                        
