# Running Celery Worker for COVU Marketplace

## Prerequisites

1. Docker Desktop installed (for Redis)
2. Python environment activated

## Install Docker Desktop (if not installed)

### Windows:

1. Download Docker Desktop: https://www.docker.com/products/docker-desktop
2. Install and restart your computer
3. Start Docker Desktop

## 🚀 Quick Start (Easiest Method)

### One-Command Startup:

```powershell
# From Backend directory, run:
.\start-dev.ps1
```

This automatically starts:

- ✅ Redis in Docker
- ✅ Django development server
- ✅ Celery worker

### Shutdown:

```powershell
.\stop-dev.ps1
```

## Manual Setup (Alternative)

### Start Redis with Docker:

```powershell
# Start Redis in Docker (one-time setup)
docker-compose up -d

# Check if Redis is running
docker ps
# Should show: covu-redis

# Test Redis connection
docker exec covu-redis redis-cli ping
# Should return: PONG
```

### Start Services (3 Terminals):

**Terminal 1 - Django Server:**

```powershell
python manage.py runserver
```

**Terminal 2 - Celery Worker:**

```powershell
celery -A covu worker --loglevel=info --pool=solo
```

### Managing Redis:

```powershell
# Stop Redis
docker-compose stop

# Start Redis
docker-compose start

# View Redis logs
docker-compose logs redis

# Restart Redis
docker-compose restart redis

# Stop and remove Redis (keeps data)
docker-compose down

# Stop and remove Redis (delete data)
docker-compose down -v
```

### Production (Linux):

```bash
# Terminal 1: Django server
gunicorn covu.wsgi:application --bind 0.0.0.0:8000

# Terminal 2: Celery worker
celery -A covu worker --loglevel=info --concurrency=4
```

## Testing Email Sending

### Test async email:

```bash
python manage.py shell
```

Then in the shell:

```python
from notifications.tasks import send_email_task

# Send test email
send_email_task.delay(
    subject='Test Email',
    message='This is a test email from Celery',
    recipient_list=['your-email@example.com']
)
```

## Monitoring Celery

### Check Celery status:

```bash
celery -A covu status
```

### Monitor tasks in real-time:

```bash
celery -A covu events
```

### Clear all tasks from queue:

```bash
celery -A covu purge
```

## Production Deployment

### Using Supervisor (Linux):

Create `/etc/supervisor/conf.d/celery.conf`:

```ini
[program:covu-celery]
command=/path/to/venv/bin/celery -A covu worker --loglevel=info
directory=/path/to/Backend
user=www-data
autostart=true
autorestart=true
stdout_logfile=/var/log/celery/worker.log
stderr_logfile=/var/log/celery/worker_error.log
```

### Using systemd (Linux):

Create `/etc/systemd/system/celery.service`:

```ini
[Unit]
Description=Celery Worker for COVU
After=network.target

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/path/to/Backend
ExecStart=/path/to/venv/bin/celery -A covu worker --loglevel=info --detach

[Install]
WantedBy=multi-user.target
```

Then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable celery
sudo systemctl start celery
sudo systemctl status celery
```

## Troubleshooting

### Celery not connecting to Redis:

1. Check Redis is running: `redis-cli ping`
2. Check REDIS_URL in .env file
3. Check firewall/port 6379

### Tasks not executing:

1. Check Celery worker logs
2. Verify task is registered: `celery -A covu inspect registered`
3. Check task queue: `celery -A covu inspect active`

### Email not sending:

1. Check Celery worker logs for errors
2. Test email settings: `python manage.py shell < test_email.py`
3. Verify SMTP credentials in .env

## Notes

- **Windows**: Use `--pool=solo` flag (required for Windows)
- **Linux**: Use `--concurrency=N` for multiple workers
- **Production**: Always use process manager (supervisor/systemd)
- **Monitoring**: Consider using Flower for web-based monitoring
