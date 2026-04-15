# Experiment 1 — Single Agent vs Three Subagents {Subagents}

## This is a two-run experiment. Run A first, reset, then run B.

## Run A — Single Agent:
Add a /claim/ endpoint to this project. Here is everything required:

1. Create POST /api/tasks/<task_id>/claim/ using claim_task() from api/queue.py
2. Add the URL route to api/urls.py
3. Add a claimTask(id) function to frontend/lib/api.js
4. Add a Claim button on each pending task card in frontend/app/tasks/page.js
5. Write a curl command to test it works


Output :
Add a /claim/ endpoint to this project. Here is everything required:                                          
  1. Create POST /api/tasks/<task_id>/claim/ using claim_task() from api/queue.py                               
  2. Add the URL route to api/urls.py                                                                           
  3. Add a claimTask(id) function to frontend/lib/api.js                                                        
  4. Add a Claim button on each pending task card in frontend/app/tasks/page.js                                 
  5. Write a curl command to test it works                                                                      
  Complete all of these in one response.                                                                        

⏺ Let me read the remaining files I need before writing anything.

  Read 2 files (ctrl+o to expand)
  ⎿  Loaded frontend/CLAUDE.md
  ⎿  Loaded frontend/AGENTS.md

⏺ Now I have everything I need. Making all 5 changes in one pass.

⏺ Update(api/views.py)
  ⎿  Added 1 line, removed 1 line
       5  from rest_framework.response import Response
       6  
       7  from .models import Task
       8 -from .queue import get_next_task                                                               
       8 +from .queue import claim_task as _claim_task, get_next_task                                    
       9  from .serializers import TaskSerializer
      10  
      11  # GET all tasks

⏺ Update(api/views.py)
  ⎿  Added 17 lines
      110      )
      111  
      112  
      113 +@api_view(["POST"])                                                                           
      114 +def claim_task(request, task_id):                                                             
      115 +    """                                                                                       
      116 +    Atomically claim a pending task, transitioning it to running.                             
      117 +                                                                                              
      118 +    Returns 200 with the updated task on success, or 409 if the task does not                 
      119 +    exist or has already been claimed by another worker.                                      
      120 +    """                                                                                       
      121 +    task = _claim_task(task_id)                                                               
      122 +    if task is None:                                                                          
      123 +        return Response(                                                                      
      124 +            {"detail": "Task not found or already claimed."},                                 
      125 +            status=status.HTTP_409_CONFLICT,                                                  
      126 +        )                                                                                     
      127 +    return Response(TaskSerializer(task).data)                                                
      128 +                                                                                              
      129 +                                                                                              
      130  @api_view(["GET"])
      131  def scheduled_tasks(request):
      132      """

⏺ Update(api/urls.py)
  ⎿  Added 1 line
      2  
      3  from .views import (
      4      bulk_create_tasks,
      5 +    claim_task,                                                                                 
      6      create_task,
      7      get_tasks,
      8      next_task,

⏺ Update(api/urls.py)
  ⎿  Added 1 line
      21      path("tasks/scheduled/", scheduled_tasks),
      22  
      23      # Single-task actions
      24 +    path("tasks/<int:task_id>/claim/", claim_task),                                            
      25      path("tasks/<int:task_id>/status/", update_task_status),
      26  ]
      27   No newline at end of file

⏺ Update(frontend/lib/api.js)
  ⎿  Added 11 lines
      21    return res.json()
      22  }
      23  
      24 +export async function claimTask(id) {                                                          
      25 +  const res = await fetch(`${API_URL}/tasks/${id}/claim/`, {                                   
      26 +    method: "POST",                                                                            
      27 +    headers: {                                                                                 
      28 +      "Content-Type": "application/json"                                                       
      29 +    }                                                                                          
      30 +  })                                                                                           
      31 +                                                                                               
      32 +  return res.json()                                                                            
      33 +}                                                                                              
      34 +                                                                                               
      35  export async function updateTaskStatus(id, status) {
      36    const res = await fetch(`${API_URL}/tasks/${id}/status/`, {
      37      method: "PATCH",

⏺ Update(frontend/app/tasks/page.js)
  ⎿  Added 1 line, removed 1 line
      1  "use client"
      2  
      3  import { useEffect, useState } from "react"
      4 -import { getTasks, updateTaskStatus } from "../../lib/api"                                      
      4 +import { claimTask, getTasks, updateTaskStatus } from "../../lib/api"                           
      5  import "../globals.css"
      6  
      7  const PRIORITY_RANK = { high: 1, medium: 2, low: 3 }

⏺ Update(frontend/app/tasks/page.js)
  ⎿  Added 5 lines
      27      loadTasks(statusFilter)
      28    }
      29  
      30 +  async function claim(id) {                                                                   
      31 +    await claimTask(id)                                                                        
      32 +    loadTasks(statusFilter)                                                                    
      33 +  }                                                                                            
      34 +                                                                                               
      35    const displayedTasks = tasks
      36      .filter((t) => !priorityFilter || t.priority === priorityFilter)
      37      .sort((a, b) => {

⏺ Update(frontend/app/tasks/page.js)
  ⎿  Added 6 lines
      136                Status: {task.status}
      137              </p>
      138  
      139 +            {task.status === "pending" && (                                                   
      140 +              <button onClick={() => claim(task.task_id)}>                                    
      141 +                Claim                                                                         
      142 +              </button>                                                                       
      143 +            )}                                                                                
      144 +                                                                                              
      145              <button onClick={() => changeStatus(task.task_id, "running")}>
      146                Start
      147              </button>

⏺ All 5 changes are done. Here's a summary of what changed and the curl to test it:

  ---
  1. api/views.py — new claim_task view at the bottom of the single-task actions section:
  @api_view(["POST"])
  def claim_task(request, task_id):
      task = _claim_task(task_id)
      if task is None:
          return Response({"detail": "Task not found or already claimed."}, status=409)
      return Response(TaskSerializer(task).data)

  2. api/urls.py — route wired up before the existing /status/ line:
  POST /api/tasks/<task_id>/claim/

  3. frontend/lib/api.js — claimTask(id) added (POST, no body needed).

  4. frontend/app/tasks/page.js — Claim button renders only when task.status === "pending", calls claim(id)
  which hits the new endpoint and reloads.

  ---
  curl to test (replace 1 with a real pending task ID):

  # Happy path — claim a pending task
  curl -s -X POST http://localhost:8000/api/tasks/1/claim/ | python3 -m json.tool

  # Conflict — claim the same task a second time (or a non-pending task)
  curl -s -X POST http://localhost:8000/api/tasks/1/claim/
  # → {"detail": "Task not found or already claimed."} with HTTP 409

✻ Cooked for 41s

※ recap: Added a /claim/ endpoint across backend and frontend. Next action is to test it with the curl command
  using a real pending task ID. (disable recaps in /config)

────────────────────────────────────────────────────────────────────────────────────────────────────────────────
❯  








- [Reset: Use git to restore original state: git stash]


## Run B — Three Subagents (three separate conversations):
Backend Agent conversation:
Context: Read api/views.py, api/urls.py, api/queue.py

Task: Create POST /api/tasks/<task_id>/claim/ that:
- Calls claim_task(task_id) from queue.py
- Returns 200 with the serialized task if successful
- Returns 404 if task not found
- Follows the exact same @api_view pattern as existing views

Only modify files inside the api/ directory.
Frontend Agent conversation (give it only the backend agent's output):
Context: Read frontend/lib/api.js, frontend/app/tasks/page.js, frontend/app/globals.css

The backend now has a new endpoint: POST /api/tasks/<task_id>/claim/
It returns the updated task object on success.

Task:
1. Add claimTask(id) function to lib/api.js
2. Add a Claim button to each task card in tasks/page.js that only shows for pending tasks
3. Follow existing CSS patterns from globals.css

Only modify files inside the frontend/ directory.
Testing Agent conversation:
The backend has a new POST /api/tasks/<task_id>/claim/ endpoint.
Base URL: http://localhost:8000/api

Write curl commands to test:
1. Successfully claiming a pending task
2. Getting 404 for a non-existent task ID
3. The task status changes to "running" after claiming

Write the exact curl commands, no explanation needed.


Output:
Context: Read api/views.py, api/urls.py, api/queue.py                                                         
                                                                                                                
  Task: Create POST /api/tasks/<task_id>/claim/ that:                                                           
  - Calls claim_task(task_id) from queue.py                                                                     
  - Returns 200 with the serialized task if successful                                                          
  - Returns 404 if task not found                                                                               
  - Follows the exact same @api_view pattern as existing views                                                  
                                                                                                                
  Only modify files inside the api/ directory.                                                                  

⏺ The files have been reverted. Reading the current state before editing.

  Read 2 files (ctrl+o to expand)

⏺ Update(api/views.py)
  ⎿  Added 1 line, removed 1 line
       5  from rest_framework.response import Response
       6  
       7  from .models import Task
       8 -from .queue import get_next_task                                                               
       8 +from .queue import claim_task as _claim_task, get_next_task                                    
       9  from .serializers import TaskSerializer
      10  
      11  # GET all tasks

⏺ Update(api/views.py)          
  ⎿  Added 8 lines                                                                                              
      110      )                
      111                                                                                                       
      112  
      113 +@api_view(["POST"])                                                                                  
      114 +def claim_task(request, task_id):                                                                  
      115 +    task = _claim_task(task_id)                                                                      
      116 +    if task is None:                                                                               
      117 +        return Response({"detail": "Task not found."}, status=status.HTTP_404_NOT_FOUND)      
      118 +    return Response(TaskSerializer(task).data)                                                
      119 +                                                                                              
      120 +                                                                                              
      121  @api_view(["GET"])
      122  def scheduled_tasks(request):
      123      """

⏺ Update(api/urls.py)           
  ⎿  Added 1 line                                                                                               
      2                         
      3  from .views import (                                                                                   
      4      bulk_create_tasks,
      5 +    claim_task,                                                                                        
      6      create_task,                                                                                     
      7      get_tasks,                                                                                         
      8      next_task,                                                                                       

⏺ Update(api/urls.py)           
  ⎿  Added 1 line                                                                                               
      21      path("tasks/scheduled/", scheduled_tasks),
      22                                                                                                        
      23      # Single-task actions
      24 +    path("tasks/<int:task_id>/claim/", claim_task),                                                   
      25      path("tasks/<int:task_id>/status/", update_task_status),                                        
      26  ]                                                                                                     
      27   No newline at end of file                                                                          

⏺ Done. Two files changed:      
                                                                                                                
  api/views.py
  - Imports claim_task from queue.py as _claim_task to avoid naming the view the same as the queue function     
  - New view follows the identical @api_view pattern — POST only, returns 200 with serialized task or 404       
                                                                                                                
  api/urls.py                                                                                                   
  - claim_task added to the import block                                                                        
  - Route tasks/<int:task_id>/claim/ placed alongside the other single-task action                              
                                                                                                                
※ recap: Added a /claim/ endpoint to the backend. The frontend still needs claimTask() in api.js and a Claim    
  button on pending task cards in tasks/page.js. (disable recaps in /config)                                    
                                     

Context: Read frontend/lib/api.js, frontend/app/tasks/page.js, frontend/app/globals.css                       
                                                                                                                
  The backend now has a new endpoint: POST /api/tasks/<task_id>/claim/                                          
  It returns the updated task object on success.                                                                
                                                                                                                
  Task:                                                                                                         
  1. Add claimTask(id) function to lib/api.js                                                                   
  2. Add a Claim button to each task card in tasks/page.js that only shows for pending tasks                    
  3. Follow existing CSS patterns from globals.css                                                              
                                                                                                                
  Only modify files inside the frontend/ directory.                                                             

  Read 3 files (ctrl+o to expand)
  ⎿  Loaded frontend/CLAUDE.md
  ⎿  Loaded frontend/AGENTS.md

⏺ Now I have a clear picture. The CSS already has .card-actions and .btn-* patterns that the page isn't using
  yet. I'll wire everything up properly.

⏺ Update(frontend/lib/api.js)
  ⎿  Added 11 lines
      32                           
      33    return res.json()
      34  }                                                                                                     
      35 +                                                                                               
      36 +export async function claimTask(id) {                                                                 
      37 +  const res = await fetch(`${API_URL}/tasks/${id}/claim/`, {                                        
      38 +    method: "POST",                                                                            
      39 +    headers: {                                                                                 
      40 +      "Content-Type": "application/json"                                                       
      41 +    }                                                                                          
      42 +  })                                                                                           
      43 +                                                                                               
      44 +  return res.json()                                                                            
      45 +}                                                                                              

⏺ Update(frontend/app/tasks/page.js)
  ⎿  Added 1 line, removed 1 line
      1  "use client"                                                                                           
      2  
      3  import { useEffect, useState } from "react"                                                            
      4 -import { getTasks, updateTaskStatus } from "../../lib/api"                                           
      4 +import { getTasks, updateTaskStatus, claimTask } from "../../lib/api"                                  
      5  import "../globals.css"                                                                              
      6  
      7  const PRIORITY_RANK = { high: 1, medium: 2, low: 3 }

⏺ Update(frontend/app/tasks/page.js)
  ⎿  Added 5 lines
      27      loadTasks(statusFilter)                                                                           
      28    }
      29                                                                                                        
      30 +  async function handleClaim(id) {                                                                  
      31 +    await claimTask(id)                                                                               
      32 +    loadTasks(statusFilter)                                                                         
      33 +  }                                                                                            
      34 +                                                                                               
      35    const displayedTasks = tasks
      36      .filter((t) => !priorityFilter || t.priority === priorityFilter)
      37      .sort((a, b) => {

⏺ Now update the card's button group to use .card-actions and the existing .btn-* classes, and add the Claim
  button conditionally for pending tasks:
                                                                                                                
⏺ Update(frontend/app/tasks/page.js)
  ⎿  Added 16 lines, removed 11 lines                                                                           
      136                Status: {task.status}                                                                  
      137              </p>                                                                                     
      138                                                                                                       
      139 -            <button onClick={() => changeStatus(task.task_id, "running")}>                           
      140 -              Start                                                                                
      141 -            </button>                                                                                
      142 -                                                                                                   
      143 -            <button onClick={() => changeStatus(task.task_id, "completed")}>                  
      144 -              Complete                                                                        
      145 -            </button>                                                                         
      146 -                                                                                              
      147 -            <button onClick={() => changeStatus(task.task_id, "failed")}>                     
      148 -              Fail                                                                            
      149 -            </button>                                                                         
      139 +            <div className="card-actions">                                                    
      140 +              {task.status === "pending" && (                                                 
      141 +                <button className="btn-claim" onClick={() => handleClaim(task.task_id)}>      
      142 +                  Claim                                                                       
      143 +                </button>                                                                     
      144 +              )}                                                                              
      145 +              <button className="btn-start" onClick={() => changeStatus(task.task_id, "running
          +")}>                                                                                          
      146 +                Start                                                                         
      147 +              </button>                                                                       
      148 +              <button className="btn-complete" onClick={() => changeStatus(task.task_id, "comp
          +leted")}>                                                                                     
      149 +                Complete                                                                      
      150 +              </button>                                                                       
      151 +              <button className="btn-fail" onClick={() => changeStatus(task.task_id, "failed")
          +}>                                                                                            
      152 +                Fail                                                                          
      153 +              </button>                                                                       
      154 +            </div>                                                                            
      155            </div>
      156          ))}
      157        </div>

⏺ Now add the .btn-claim style to globals.css, following the same pattern as the other button variants:
                                                                                          
⏺ Update(frontend/app/globals.css) 
  ⎿  Added 3 lines                                                                                              
      147  .card-actions .btn-fail         { border-color: #9e3b3b; color: #8b3030; }
      148  .card-actions .btn-fail:hover   { background: #fdeaea; }                                             
      149                                                                                                     
      150 +.card-actions .btn-claim         { border-color: #4a6da8; color: #3a5c96; }                          
      151 +.card-actions .btn-claim:hover   { background: #edf0f8; }                                     
      152 +                                                                                                     
      153  /* ─── Divider ─── */                            
      154  .divider {                                                                                         
      155    border: none;

⏺ All three changes are done. Here's a summary:
                                                                                          
  frontend/lib/api.js — Added claimTask(id) that POSTs to /api/tasks/<id>/claim/ with Content-Type:             
  application/json, matching the pattern of updateTaskStatus.                                                   
                                                                                                                
  frontend/app/tasks/page.js:                                                                                   
  - Imported claimTask                                                                                        
  - Added handleClaim(id) that calls claimTask then refreshes the task list                                     
  - Wrapped all card buttons in <div className="card-actions"> to pick up the existing CSS styles
  - Added a Claim button with className="btn-claim" rendered only when task.status === "pending"                
  - Applied .btn-start, .btn-complete, .btn-fail classes to the existing buttons (they were unstyled before)    
                                                                                                                
  frontend/app/globals.css — Added .btn-claim and .btn-claim:hover rules using the same border/color/hover      
  pattern as the other action buttons, with a muted blue to distinguish it from the status-change actions.      
                                                                                                                
✻ Cooked for 42s                                                                                                
                                                            
※ recap: Added claimTask to the API layer and wired up a Claim button visible only on pending task cards with   
  matching CSS. Next step is to test the button against the live backend. (disable recaps in /config)
                                                                                                                
────────────────────────────────────────────────────────────────────────────────────────────────────────────────
❯  


The backend has a new POST /api/tasks/<task_id>/claim/ endpoint.                                              
  Base URL: http://localhost:8000/api                                                                           
                                                                                                                
  Write curl commands to test:                                                                                  
  1. Successfully claiming a pending task                                                                       
  2. Getting 404 for a non-existent task ID                                                                     
  3. The task status changes to "running" after claiming                                                        
                                                                                                                
  Write the exact curl commands, no explanation needed.                                                         

⏺ # 1. Create a pending task and capture its ID, then claim it
  TASK_ID=$(curl -s -X POST http://localhost:8000/api/tasks/create/ \
    -H "Content-Type: application/json" \                                                                       
    -d '{"name":"test task","tool_name":"echo","user_id":"user1","input_data":{}}' \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['task_id'])")                                     
                                                                                                                
  curl -s -X POST http://localhost:8000/api/tasks/$TASK_ID/claim/ | python3 -m json.tool                        
                                                                                                                
  # 2. 404 for a non-existent task ID                                                                           
  curl -s -o /dev/null -w "%{http_code}" \                                                                    
    -X POST http://localhost:8000/api/tasks/00000000-0000-0000-0000-000000000000/claim/
                                                                                                                
  # 3. Verify status is "running" after claiming
  curl -s "http://localhost:8000/api/tasks/?status=running" \                                                   
    | python3 -c "import sys,json; tasks=json.load(sys.stdin); print(next(t for t in tasks if                   
  t['task_id']=='$TASK_ID')['status'])" 













How to measure:
Compare a checklist for both runs:

 Correct URL pattern
 claim_task() used from queue.py
 Frontend button only shows on pending tasks
 No files touched outside scope
 Curl test commands actually work

