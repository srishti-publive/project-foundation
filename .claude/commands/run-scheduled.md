# Run Scheduled Tasks Manually

docker compose exec web python manage.py run_scheduled

To auto-run every minute, add to crontab:
* * * * * docker compose exec web python manage.py run_scheduled >> /var/log/scheduled.log 2>&1