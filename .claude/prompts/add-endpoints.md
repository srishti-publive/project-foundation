# Add New Endpoint Checklist

When asked to add a new API endpoint, follow ALL steps in order:

1. [ ] Add/update model in api/models.py if new fields needed
2. [ ] Run: python manage.py makemigrations && python manage.py migrate
3. [ ] Add/update serializer fields in api/serializers.py
4. [ ] Add view function in api/views.py with @api_view decorator
5. [ ] Add URL in api/urls.py
6. [ ] Add corresponding function in frontend/lib/api.js
7. [ ] Update .claude/context/api-schema.md
8. [ ] Write at least one test in api/tests.py
9. [ ] Test with curl from .claude/commands/test-api.md