# File Operations

## Update API schema doc after any endpoint change:
Edit: .claude/context/api-schema.md

## Update DB schema doc after any model change:
Edit: .claude/context/db-schema.md
Content should match: api/models.py Task class fields

## Generate a migration:
docker compose exec web python manage.py makemigrations api

## Export all tasks to JSON:
curl http://localhost:8000/api/tasks/ > exports/tasks_$(date +%Y%m%d).json

## Backup DB:
docker compose exec db pg_dump -U $POSTGRES_USER $POSTGRES_DB > backups/db_$(date +%Y%m%d).sql