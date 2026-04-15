Run Django migrations inside Docker:
```bash
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate
```