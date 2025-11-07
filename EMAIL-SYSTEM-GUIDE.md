# 🎯 COVU Email System - Complete Setup Guide

## 📋 Overview

Your COVU marketplace now has a **production-ready email system** that:

- ✅ Sends emails **asynchronously** (doesn't block user requests)
- ✅ **Auto-retries** failed emails (3 attempts with backoff)
- ✅ Uses **Redis in Docker** (works on Windows!)
- ✅ Handles **SSL properly** (certifi package)
- ✅ **Production-ready** with proper error handling

## 🚀 Getting Started (3 Steps)

### Step 1: Install Docker Desktop

1. Download: https://www.docker.com/products/docker-desktop
2. Install and restart PC
3. Start Docker Desktop

### Step 2: Start Everything

```powershell
cd C:\Users\DELL\Desktop\Backend
.\start-dev.ps1
```

This opens 3 terminals:

- **Terminal 1**: Status/Info
- **Terminal 2**: Django (http://localhost:8000)
- **Terminal 3**: Celery (email worker)

### Step 3: Test It

```powershell
.\test-email.ps1
```

## 📁 Files Overview

| File                    | Purpose                 |
| ----------------------- | ----------------------- |
| `docker-compose.yml`    | Redis container config  |
| `start-dev.ps1`         | **One-command startup** |
| `stop-dev.ps1`          | Shutdown script         |
| `test-email.ps1`        | Test email system       |
| `DOCKER-REDIS-SETUP.md` | Detailed Docker guide   |
| `CELERY-SETUP.md`       | Celery production guide |

## 🔧 Configuration

Your `.env` file should have:

```env
# Email Configuration
EMAIL_BACKEND=covu.email_backend.CustomEmailBackend
EMAIL_HOST=smtp.zoho.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=covumarket@covumarket.com
EMAIL_HOST_PASSWORD=1998Runs.
DEFAULT_FROM_EMAIL=covumarket@covumarket.com

# Redis (for Celery)
REDIS_URL=redis://localhost:6379/0
```

## 📧 Email Notifications

Your system automatically sends emails for:

1. **Order Created** - Customer receives order confirmation
2. **Order Accepted** - Customer notified when seller accepts
3. **Order Delivered** - Delivery confirmation
4. **Payment Received** - Payment confirmation
5. **Order Cancelled** - Cancellation notification

## 🎮 Daily Usage

### Start Development:

```powershell
.\start-dev.ps1
```

### Stop Development:

```powershell
# Stop Redis
.\stop-dev.ps1

# Stop Django/Celery: Press Ctrl+C in their terminals
```

### View What's Running:

```powershell
# Check Redis
docker ps

# Check Celery tasks
celery -A covu inspect active
```

## 🧪 Testing

### Test Email Queue:

```python
# In Django shell (python manage.py shell)
from notifications.tasks import send_email_task

send_email_task.delay(
    subject='Test Email',
    message='Testing Celery!',
    recipient_list=['your-email@example.com']
)
```

### Monitor Celery:

Watch the **Celery terminal** - you'll see:

```
[2025-11-07 10:30:15,123: INFO/MainProcess] Task notifications.tasks.send_email_task[abc-123] received
[2025-11-07 10:30:16,456: INFO/MainProcess] Task notifications.tasks.send_email_task[abc-123] succeeded
```

## 🐛 Troubleshooting

### Issue: "Docker is not running"

**Solution**: Start Docker Desktop, wait for whale icon to be stable

### Issue: "Cannot connect to Redis"

**Solution**:

```powershell
docker-compose up -d
docker exec covu-redis redis-cli ping  # Should return PONG
```

### Issue: "Emails not sending"

**Solution**:

1. Check Celery terminal for errors
2. Verify `.env` has correct SMTP credentials
3. Test with: `.\test-email.ps1`

### Issue: "Celery tasks stuck"

**Solution**:

```powershell
# Clear all tasks
celery -A covu purge

# Restart Celery worker (Ctrl+C and restart)
celery -A covu worker --loglevel=info --pool=solo
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│           Windows (Your PC)             │
├─────────────────────────────────────────┤
│                                         │
│  ┌──────────────┐  ┌─────────────────┐ │
│  │   Django     │  │  Celery Worker  │ │
│  │   :8000      │──│  (async tasks)  │ │
│  └──────────────┘  └─────────────────┘ │
│         │                    │          │
│         └────────┬───────────┘          │
│                  │                      │
│         ┌────────▼────────┐             │
│         │  Docker Desktop │             │
│         │  ┌────────────┐ │             │
│         │  │   Redis    │ │             │
│         │  │ :6379 (🐧) │ │             │
│         │  └────────────┘ │             │
│         └─────────────────┘             │
│                                         │
└─────────────────────────────────────────┘
            │
            │ SMTP
            ▼
    ┌──────────────┐
    │ Zoho Email   │
    │ smtp.zoho.com│
    └──────────────┘
```

## 📊 What Happens When Order is Created

```
1. User creates order
   ↓
2. Django saves order to database
   ↓
3. Django queues email task to Celery
   ↓ (returns immediately - no waiting!)
4. User sees success message

   Meanwhile (async):
   ↓
5. Celery picks up task from Redis
   ↓
6. Celery sends email via Zoho SMTP
   ↓
7. If fails: Auto-retry (up to 3 times)
   ↓
8. Email delivered! ✅
```

## 🚀 Production Deployment

For production (Linux server):

1. **Keep docker-compose.yml** for Redis
2. **Use Supervisor/Systemd** for Celery
3. **Update .env** with production values
4. **Set DEBUG=False**

See `CELERY-SETUP.md` for detailed production setup.

## ✅ Benefits of This Setup

| Feature              | Benefit                             |
| -------------------- | ----------------------------------- |
| **Async Email**      | Orders don't wait for email to send |
| **Auto-retry**       | Failed emails retry automatically   |
| **Docker Redis**     | Works on Windows without WSL        |
| **SSL/TLS**          | Secure email with certifi           |
| **Monitoring**       | Watch tasks in Celery terminal      |
| **Production-ready** | Same code works in production       |

## 📚 Additional Resources

- **Docker Setup**: See `DOCKER-REDIS-SETUP.md`
- **Celery Guide**: See `CELERY-SETUP.md`
- **Test Script**: Run `.\test-email.ps1`

## 🎉 Summary

You now have:

- ✅ Redis running in Docker (Linux environment)
- ✅ Celery worker processing emails asynchronously
- ✅ Automatic retry on failures
- ✅ Production-ready SSL/TLS
- ✅ One-command startup: `.\start-dev.ps1`

**Next Steps:**

1. Run `.\start-dev.ps1`
2. Create a test order
3. Watch email send in Celery terminal!

---

_Made with ❤️ for COVU Marketplace_
