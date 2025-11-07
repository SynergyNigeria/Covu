# 🎯 Quick Start - COVU Development

## For Impatient Developers 😎

```powershell
# 1. Start everything
.\start-dev.ps1

# 2. Test emails
.\test-email.ps1

# 3. Build something awesome! 🚀
```

That's it! Your async email system is running.

---

## First Time Setup

### 1. Install Docker Desktop (One Time)

- Download: https://www.docker.com/products/docker-desktop
- Install → Restart PC → Start Docker Desktop
- Wait for whale icon 🐳 to be stable

### 2. Verify Setup

```powershell
# Check Docker
docker --version

# Check Python packages
pip list | Select-String "celery|redis"
# Should show: celery, redis, certifi
```

---

## Daily Workflow

### Start Development (Morning ☕)

```powershell
cd C:\Users\DELL\Desktop\Backend
.\start-dev.ps1
```

**Opens 3 terminals:**

1. Main - Status info
2. Django - http://localhost:8000
3. Celery - Email worker

### Work on Features (All Day 💻)

- Edit code
- Django auto-reloads
- Emails send async via Celery
- Orders don't wait for emails

### Stop Development (Evening 🌙)

```powershell
# Stop Redis
.\stop-dev.ps1

# Stop Django/Celery: Ctrl+C in their terminals
```

---

## Common Tasks

### View Running Services

```powershell
# Check all Docker containers
docker ps

# Check Redis specifically
docker exec covu-redis redis-cli ping
# Returns: PONG

# Check Celery tasks
celery -A covu inspect active
```

### Monitor Email Sending

**Watch the Celery terminal** - you'll see:

```
Task notifications.tasks.send_email_task[abc123] received
Email sent successfully to: customer@example.com
Task notifications.tasks.send_email_task[abc123] succeeded
```

### Test Email System

```powershell
# Quick test
.\test-email.ps1

# Or manually in Django shell
python manage.py shell
```

```python
from notifications.tasks import send_email_task
send_email_task.delay(
    subject='Test',
    message='Testing!',
    recipient_list=['test@example.com']
)
```

### Clear Stuck Tasks

```powershell
celery -A covu purge
# Clears all pending tasks
```

### Restart Services

```powershell
# Restart Redis
docker-compose restart redis

# Restart Celery: Ctrl+C in terminal, then:
celery -A covu worker --loglevel=info --pool=solo

# Restart Django: Ctrl+C in terminal, then:
python manage.py runserver
```

---

## Troubleshooting

### "Docker is not running"

→ Start Docker Desktop, wait for whale icon

### "Cannot connect to Redis"

```powershell
docker-compose up -d
docker ps  # Should see covu-redis
```

### "Emails not sending"

1. Check `.env` file (SMTP credentials)
2. Check Celery terminal (errors?)
3. Run: `.\test-email.ps1`

### "Port 8000 already in use"

```powershell
# Find what's using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID)
taskkill /PID <PID> /F
```

### "Port 6379 already in use"

```powershell
# Stop any Redis containers
docker-compose down

# Restart
docker-compose up -d
```

---

## File Structure

```
Backend/
├── start-dev.ps1           ← 🚀 START HERE
├── stop-dev.ps1            ← Stop services
├── test-email.ps1          ← Test emails
├── docker-compose.yml      ← Redis config
├── EMAIL-SYSTEM-GUIDE.md   ← Full guide
├── DOCKER-REDIS-SETUP.md   ← Docker details
└── CELERY-SETUP.md         ← Production guide
```

---

## What You Built

✅ **Async Email System**

- Orders create instantly
- Emails send in background
- Auto-retry on failures

✅ **Production-Ready**

- SSL/TLS with certifi
- Error handling
- Redis task queue

✅ **Windows-Compatible**

- Redis in Docker (Linux)
- Django on Windows
- Celery on Windows

---

## Next Steps

1. **Start dev**: `.\start-dev.ps1`
2. **Create order** on http://localhost:8000
3. **Watch email** send in Celery terminal
4. **Build features** - emails just work!

---

## Resources

| Question           | Answer                      |
| ------------------ | --------------------------- |
| How does it work?  | See `EMAIL-SYSTEM-GUIDE.md` |
| Docker setup?      | See `DOCKER-REDIS-SETUP.md` |
| Production deploy? | See `CELERY-SETUP.md`       |
| Quick test?        | Run `.\test-email.ps1`      |

---

**Pro Tip**: Keep the 3 terminals visible in split view to monitor everything! 👀

_Now go build something awesome! 🚀_
