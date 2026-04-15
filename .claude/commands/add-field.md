# Add a Field to Task Model

1. Edit api/models.py — add the field
2. Run: docker compose exec web python manage.py makemigrations
3. Run: docker compose exec web python manage.py migrate
4. Update api/serializers.py if needed
5. Update .claude/context/db-schema.md