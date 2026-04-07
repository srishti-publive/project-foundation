from django.urls import path
from .views import get_tasks, create_task

urlpatterns = [
    path("tasks/", get_tasks),
    path("tasks/create/", create_task),
]