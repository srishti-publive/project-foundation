# Claim a Task

Add a POST /api/tasks/<id>/claim/ endpoint that calls claim_task() from api/queue.py.

Steps:
1. Add claim_task view in api/views.py using the existing claim_task() function
2. Add URL pattern in api/urls.py: path('tasks/<int:task_id>/claim/', views.claim_task_view)
3. Add claimTask(id) to frontend/lib/api.js
4. Run: docker compose exec web python manage.py test api