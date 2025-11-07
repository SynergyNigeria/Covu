# 🚀 COVU Development Setup with Docker

## What This Does

This setup runs **Redis in Docker** (Linux environment) while keeping Django and Celery on your Windows machine. This solves the "Redis doesn't work on Windows" problem!

## Files Created

- `docker-compose.yml` - Redis container configuration
- `start-dev.ps1` - One-command startup script
- `stop-dev.ps1` - Shutdown script
- `.dockerignore` - Excludes unnecessary files from Docker

## Prerequisites

1. **Docker Desktop** - Download: https://www.docker.com/products/docker-desktop
2. **Python environment** - Already activated
3. **Celery installed** - Already done (`pip install celery redis`)

## 🎯 Quick Start

### First Time Setup:

1. **Install Docker Desktop** (if not installed)

   - Download and install from link above
   - Restart your computer
   - Start Docker Desktop and wait for it to be ready

2. **Start Everything**:

   ```powershell
   cd C:\Users\DELL\Desktop\Backend
   .\start-dev.ps1
   ```

3. **Access Your App**:
   - Django: http://localhost:8000
   - Redis: Running on localhost:6379
   - Celery: Running in background terminal

### Daily Usage:

```powershell
# Start all services
.\start-dev.ps1

# Stop Redis (Celery/Django: Ctrl+C in their terminals)
.\stop-dev.ps1
```

## What Happens When You Start?

```
start-dev.ps1 runs:
├── ✅ Starts Redis in Docker container
├── ✅ Opens new terminal → Django server
└── ✅ Opens new terminal → Celery worker

Result: 3 terminals running:
1. Main terminal - Shows startup info
2. Django terminal - http://localhost:8000
3. Celery terminal - Async task processing
```

## Manual Commands

### Redis Management:

```powershell
# Start Redis
docker-compose up -d

# Check if running
docker ps

# View logs
docker-compose logs redis

# Stop Redis
docker-compose stop

# Remove container (keeps data)
docker-compose down

# Remove container and data
docker-compose down -v
```

### Test Redis Connection:

```powershell
# Test from outside container
docker exec covu-redis redis-cli ping
# Returns: PONG

# Enter Redis CLI
docker exec -it covu-redis redis-cli

# Inside Redis CLI:
> PING
> KEYS *
> GET some_key
> exit
```

### Django & Celery:

```powershell
# Django server (manual)
python manage.py runserver

# Celery worker (manual)
celery -A covu worker --loglevel=info --pool=solo
```

## Testing Email System

### Test Async Email:

```powershell
python manage.py shell
```

```python
from notifications.tasks import send_email_task

# Queue an email
send_email_task.delay(
    subject='Test Email',
    message='This is a test from Celery!',
    recipient_list=['test@example.com']
)

# You'll see it processing in the Celery terminal!
```

### Monitor Celery:

```powershell
# Check active tasks
celery -A covu inspect active

# Check registered tasks
celery -A covu inspect registered

# Purge all tasks
celery -A covu purge
```

## Troubleshooting

### "Docker is not running"

- Start Docker Desktop
- Wait for whale icon to be stable (not animated)
- Run `docker info` to verify

### "Cannot connect to Redis"

- Check Docker container: `docker ps`
- Should see `covu-redis` running
- Test connection: `docker exec covu-redis redis-cli ping`

### "Celery tasks not executing"

- Check Celery terminal for errors
- Verify Redis is running
- Check `.env` has: `REDIS_URL=redis://localhost:6379/0`

### "Email not sending"

- Check Celery worker logs
- Verify SMTP settings in `.env`:
  - `EMAIL_HOST=smtp.zoho.com`
  - `EMAIL_HOST_USER=covumarket@covumarket.com`
  - `EMAIL_HOST_PASSWORD=1998Runs.`

## Production Deployment

For production (Linux server), you can:

1. **Use same docker-compose.yml** for Redis
2. **Add Django and Celery** to docker-compose (optional)
3. **Use Supervisor/Systemd** for process management

See `CELERY-SETUP.md` for production deployment details.

## Why Docker for Redis?

✅ **Cross-platform**: Redis runs in Linux container on Windows
✅ **Production-like**: Same Redis version in dev and prod
✅ **Easy cleanup**: `docker-compose down -v` removes everything
✅ **Persistent data**: Data saved even after container restarts
✅ **One command**: `docker-compose up -d` and you're ready

## Architecture

```
Windows (Your PC)
├── Docker Desktop
│   └── Linux Container
│       └── Redis Server (port 6379)
├── Django (Python)
│   └── Runs on Windows directly
└── Celery Worker (Python)
    └── Connects to Redis in Docker
    └── Sends emails asynchronously
```

## Summary

- **Development**: Use `start-dev.ps1` (easiest)
- **Redis**: Runs in Docker (Linux environment)
- **Django/Celery**: Run on Windows (your Python)
- **Emails**: Async via Celery with auto-retry
- **SSL**: Handled with certifi package
- **Cleanup**: `stop-dev.ps1` or `docker-compose down`

🎉 You now have a production-ready async email system running on Windows!
