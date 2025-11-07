# 🚀 COVU Email System - Documentation Index

## 🎯 Start Here

**New to the project?** → Read `SETUP-COMPLETE.md`

**Want to start coding?** → Run `.\start-dev.ps1`

**Having issues?** → Run `.\check-status.ps1`

---

## 📚 Documentation Guide

### For Developers (Daily Use)

1. **README-DEV.md**

   - Quick start guide
   - Daily workflow
   - Common tasks
   - 👉 **Start here if you just want to code!**

2. **Scripts to Use:**
   ```powershell
   .\start-dev.ps1     # Start everything (one command!)
   .\check-status.ps1  # Check if all services running
   .\test-email.ps1    # Test email system
   .\stop-dev.ps1      # Stop Redis
   ```

### For Understanding the System

3. **SETUP-COMPLETE.md**

   - Complete overview
   - Architecture diagrams
   - Email flow explained
   - 👉 **Read this to understand how everything works**

4. **EMAIL-SYSTEM-GUIDE.md**
   - Email system details
   - Configuration explained
   - Monitoring and testing
   - Production benefits

### For Docker & Redis

5. **DOCKER-REDIS-SETUP.md**
   - Why Docker for Redis
   - Docker commands
   - Redis management
   - Troubleshooting Docker issues

### For Production Deployment

6. **CELERY-SETUP.md**
   - Production deployment
   - Supervisor/Systemd setup
   - Monitoring with Flower
   - Production best practices

---

## 🛠️ Quick Reference

### System Architecture

```
Windows PC
├── Docker → Redis (Linux container)
├── Django → API Server
└── Celery → Email Worker
```

### Services & Ports

- **Django**: http://localhost:8000
- **Redis**: localhost:6379
- **Celery**: Background worker (no port)

### Email Flow

```
Order Created → Queue to Redis → Celery Sends → Auto-retry if fail
```

---

## 📂 File Structure

```
Backend/
├── 🚀 START HERE
│   ├── start-dev.ps1           ← Run this first!
│   ├── README-DEV.md           ← Quick start guide
│   └── SETUP-COMPLETE.md       ← Full overview
│
├── 🛠️ UTILITIES
│   ├── check-status.ps1        ← Health check
│   ├── test-email.ps1          ← Test emails
│   └── stop-dev.ps1            ← Shutdown
│
├── 🐳 DOCKER
│   ├── docker-compose.yml      ← Redis config
│   ├── .dockerignore           ← Docker exclusions
│   └── DOCKER-REDIS-SETUP.md   ← Docker guide
│
├── 📧 EMAIL SYSTEM
│   ├── EMAIL-SYSTEM-GUIDE.md   ← Email details
│   ├── covu/email_backend.py   ← Custom SMTP backend
│   ├── notifications/tasks.py   ← Celery tasks
│   └── notifications/services.py ← Email logic
│
├── ⚙️ CELERY
│   ├── CELERY-SETUP.md         ← Production guide
│   ├── covu/celery.py          ← Celery config
│   └── covu/__init__.py        ← Celery import
│
└── 📚 THIS FILE
    └── DOCUMENTATION-INDEX.md   ← You are here!
```

---

## 🎯 Common Scenarios

### "I just cloned the repo"

1. Install Docker Desktop
2. Activate Python venv
3. Run: `.\start-dev.ps1`
4. Read: `README-DEV.md`

### "I want to start coding"

```powershell
.\start-dev.ps1     # Start services
# Code away! 🚀
```

### "Something's not working"

```powershell
.\check-status.ps1  # Check what's wrong
# Follow the suggestions
```

### "I want to test emails"

```powershell
.\test-email.ps1    # Quick test

# Or manually:
python manage.py shell
# Then: from notifications.tasks import send_email_task
```

### "I need to deploy to production"

1. Read: `CELERY-SETUP.md`
2. Read: `DOCKER-REDIS-SETUP.md` (production sections)
3. Update `.env` with production values
4. Set `DEBUG=False`

### "I want to understand the architecture"

1. Read: `SETUP-COMPLETE.md` (architecture section)
2. Read: `EMAIL-SYSTEM-GUIDE.md` (flow diagrams)

---

## ✅ Setup Checklist

- [ ] Docker Desktop installed
- [ ] Python venv activated
- [ ] Packages installed (celery, redis, certifi)
- [ ] `.env` file configured
- [ ] Run `.\start-dev.ps1` successfully
- [ ] Run `.\check-status.ps1` - all green ✅
- [ ] Run `.\test-email.ps1` - email queued
- [ ] Create test order - watch Celery terminal

---

## 🆘 Help & Support

### Quick Fixes

| Issue                | Fix                      |
| -------------------- | ------------------------ |
| Docker not running   | Start Docker Desktop     |
| Redis not connecting | `docker-compose up -d`   |
| Port already in use  | Check `netstat -ano`     |
| Emails not sending   | Check `.env` credentials |
| Celery stuck         | `celery -A covu purge`   |

### Detailed Troubleshooting

- **Docker issues** → See `DOCKER-REDIS-SETUP.md`
- **Email issues** → See `EMAIL-SYSTEM-GUIDE.md`
- **Celery issues** → See `CELERY-SETUP.md`
- **General issues** → See `README-DEV.md`

---

## 📖 Documentation Standards

All documentation files follow this structure:

1. **Overview** - What this doc covers
2. **Quick Start** - Get going fast
3. **Details** - Deep dive
4. **Troubleshooting** - Common issues
5. **Examples** - Practical usage

---

## 🔄 Keeping Documentation Updated

When you make changes:

- Update relevant `.md` files
- Update this index if adding new docs
- Keep code comments in sync
- Test all scripts after changes

---

## 💡 Tips

- **Bookmark this file** - Central hub for all docs
- **Read README-DEV.md first** - Fastest way to start
- **Use scripts** - Don't memorize commands
- **Check status often** - `.\check-status.ps1` is your friend

---

## 🎓 Learning Path

1. **Day 1**: Read `README-DEV.md`, run `.\start-dev.ps1`
2. **Day 2**: Read `SETUP-COMPLETE.md`, understand architecture
3. **Day 3**: Read `EMAIL-SYSTEM-GUIDE.md`, test emails
4. **Day 4**: Read `DOCKER-REDIS-SETUP.md`, explore Docker
5. **Week 2**: Read `CELERY-SETUP.md`, prepare for production

---

**Happy Coding! 🚀**

_Last Updated: November 7, 2025_
