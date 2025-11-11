# COVU Deployment Guide for Render

## Overview

Render provides free PostgreSQL database and makes deployment simple with automatic builds from GitHub.

## Prerequisites

- GitHub account with your COVU repository
- Render account (sign up at https://render.com)

## Step 1: Prepare Your Repository

### 1.1 Create `build.sh` (Build Script)

Create a file named `build.sh` in your Backend folder:

```bash
#!/usr/bin/env bash
# exit on error
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate
```

Make it executable:

```bash
chmod +x build.sh
```

### 1.2 Create `render.yaml` (Optional - Infrastructure as Code)

Create `render.yaml` in your Backend folder:

```yaml
databases:
  - name: covu-db
    databaseName: covu_db
    user: covu_user
    plan: free

services:
  - type: web
    name: covu-backend
    runtime: python
    buildCommand: "./build.sh"
    startCommand: "gunicorn covu.wsgi:application"
    envVars:
      - key: PYTHON_VERSION
        value: 3.11
      - key: DATABASE_URL
        fromDatabase:
          name: covu-db
          property: connectionString
      - key: SECRET_KEY
        generateValue: true
      - key: DEBUG
        value: False
```

### 1.3 Update requirements.txt

Add Gunicorn and WhiteNoise for production:

```bash
# Add to requirements.txt
gunicorn==21.2.0
whitenoise==6.6.0
```

### 1.4 Update settings.py for Render

Add at the top of `covu/settings.py` (after imports):

```python
import os
import dj_database_url
```

Update database configuration:

```python
# Database configuration for Render
if 'DATABASE_URL' in os.environ:
    # Render PostgreSQL
    DATABASES = {
        'default': dj_database_url.config(
            default=os.environ.get('DATABASE_URL'),
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
elif config("USE_POSTGRESQL", default=False, cast=bool):
    # Manual PostgreSQL configuration
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": config("POSTGRES_DB", default="covu_db"),
            "USER": config("POSTGRES_USER", default="postgres"),
            "PASSWORD": config("POSTGRES_PASSWORD"),
            "HOST": config("POSTGRES_HOST", default="localhost"),
            "PORT": config("POSTGRES_PORT", default="5432"),
            "CONN_MAX_AGE": 600,
            "OPTIONS": {
                "connect_timeout": 10,
            },
        }
    }
else:
    # SQLite for local development
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
```

Add static files configuration:

```python
# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = []

# WhiteNoise - Serve static files efficiently
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

Update ALLOWED_HOSTS:

```python
# In production, Render provides the app URL
ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default="localhost,127.0.0.1,.onrender.com"
).split(",")
```

### 1.5 Add dj-database-url to requirements.txt

```bash
# Add this line
dj-database-url==2.1.0
```

### 1.6 Push to GitHub

```bash
git add .
git commit -m "Prepare for Render deployment"
git push origin master
```

## Step 2: Create PostgreSQL Database on Render

1. Go to https://dashboard.render.com
2. Click **"New +"** → **"PostgreSQL"**
3. Configure database:
   - **Name**: `covu-db`
   - **Database**: `covu_db`
   - **User**: `covu_user` (auto-generated)
   - **Region**: Choose closest to your users (e.g., Frankfurt for Europe)
   - **Plan**: **Free** (for testing) or **Starter** ($7/month for production)
4. Click **"Create Database"**
5. Wait for database to provision (~2 minutes)
6. **Copy the Internal Database URL** (we'll use this in the web service)

## Step 3: Create Web Service on Render

1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub repository
3. Configure web service:

   - **Name**: `covu-backend`
   - **Region**: Same as database
   - **Branch**: `master`
   - **Root Directory**: `Backend` (if your Django project is in a subfolder)
   - **Runtime**: `Python 3`
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn covu.wsgi:application --bind 0.0.0.0:$PORT`
   - **Plan**: **Free** (for testing) or **Starter** ($7/month)

4. Click **"Advanced"** to add environment variables

## Step 4: Configure Environment Variables

Add these environment variables in Render dashboard:

```env
# Django
SECRET_KEY=<click Generate to create a random secret key>
DEBUG=False
ALLOWED_HOSTS=.onrender.com
PYTHON_VERSION=3.11

# Database (automatically set by Render if you linked the database)
DATABASE_URL=<internal database URL from Step 2>

# Paystack
PAYSTACK_SECRET_KEY=sk_live_c93e17e4988a55974a0d5faa937d3e9996b59b5d
PAYSTACK_PUBLIC_KEY=pk_live_7e0bd07296e05a65c1442481dfc352b723cf5a5c
PAYSTACK_WEBHOOK_SECRET=<your_webhook_secret>

# Frontend (update with your actual frontend URL)
FRONTEND_URL=https://your-frontend-url.com
CORS_ALLOWED_ORIGINS=https://your-frontend-url.com

# Email
EMAIL_BACKEND=covu.email_backend.CustomEmailBackend
EMAIL_HOST=smtp.zoho.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=covumarket@covumarket.com
EMAIL_HOST_PASSWORD=1998Runs.
DEFAULT_FROM_EMAIL=COVU Marketplace <covumarket@covumarket.com>

# Cloudinary
CLOUDINARY_CLOUD_NAME=dpmxcjkfl
CLOUDINARY_API_KEY=126559825358577
CLOUDINARY_API_SECRET=PCPdR7La2s_H0A3bfTnOZNFUH44

# Sentry
SENTRY_DSN=https://5c8935e3785f8163f193f27406fde70b@o4510223879110656.ingest.de.sentry.io/4510223884877904

# Redis (optional - add Redis service if needed)
# REDIS_URL=<redis_url_from_render>
# CELERY_BROKER_URL=<redis_url_from_render>
```

## Step 5: Deploy

1. Click **"Create Web Service"**
2. Render will automatically:
   - Clone your repository
   - Install dependencies
   - Run migrations
   - Collect static files
   - Start your application
3. Wait for deployment (~5-10 minutes for first deploy)
4. Your app will be available at: `https://covu-backend.onrender.com`

## Step 6: Create Superuser

After deployment, use Render Shell:

1. Go to your web service dashboard
2. Click **"Shell"** tab
3. Run:

```bash
python manage.py createsuperuser
```

## Step 7: Configure Paystack Webhook

1. Get your Render URL: `https://covu-backend.onrender.com`
2. Go to Paystack Dashboard → Settings → Webhooks
3. Add webhook URL: `https://covu-backend.onrender.com/api/wallet/paystack-webhook/`
4. Copy the webhook secret and add it to Render environment variables

## Step 8: Deploy Frontend to Render

### 8.1 Create Frontend Web Service

1. Click **"New +"** → **"Static Site"**
2. Connect your GitHub repository
3. Configure:
   - **Name**: `covu-frontend`
   - **Branch**: `master`
   - **Root Directory**: `frontend`
   - **Build Command**: Leave empty (static files)
   - **Publish Directory**: `.`

### 8.2 Update Frontend API URLs

Update `frontend/assets/js/config.js`:

```javascript
const API_CONFIG = {
  BASE_URL: "https://covu-backend.onrender.com/api",
  // ... rest of config
};
```

### 8.3 Update CORS in Backend

Update Render environment variable:

```
CORS_ALLOWED_ORIGINS=https://covu-frontend.onrender.com
```

## Render Free Tier Limitations

⚠️ **Important Notes about Free Tier:**

1. **Web Service Spins Down**: Free services sleep after 15 minutes of inactivity

   - First request after sleep takes ~30-60 seconds to wake up
   - Solution: Upgrade to Starter plan ($7/month) or use a service like UptimeRobot to ping your app

2. **PostgreSQL Free Tier**:

   - 1GB storage
   - Expires after 90 days
   - Solution: Upgrade to Starter plan ($7/month) for production

3. **Build Minutes**: 500 build minutes/month on free tier

## Monitoring & Maintenance

### View Logs

- Go to your service dashboard
- Click **"Logs"** tab
- View real-time logs

### Manual Deploy

- Click **"Manual Deploy"** → **"Deploy latest commit"**

### Database Backups

1. Go to your database dashboard
2. Click **"Backups"** tab
3. Create manual backup or configure automatic daily backups

### Performance Monitoring

- Use Sentry (already configured) for error tracking
- Render provides basic metrics in the dashboard

## Troubleshooting

### Issue: "Application failed to respond"

**Solution**: Check logs for errors. Common causes:

- Migration failed
- Environment variables missing
- Database connection issue

### Issue: "Static files not loading"

**Solution**:

```bash
# In Render Shell
python manage.py collectstatic --no-input
```

### Issue: "Database connection refused"

**Solution**: Ensure `DATABASE_URL` environment variable is correctly set from the PostgreSQL database

### Issue: "CORS errors"

**Solution**: Update `CORS_ALLOWED_ORIGINS` to include your frontend URL

## Cost Estimation

### Development/Testing (Free):

- Web Service: Free
- PostgreSQL: Free (90 days)
- **Total**: $0/month

### Production (Recommended):

- Web Service: Starter ($7/month)
- PostgreSQL: Starter ($7/month)
- Redis (optional): Starter ($7/month)
- **Total**: $14-21/month

## Alternative: Using Docker (Advanced)

If you want to use Docker on Render:

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --no-input

CMD gunicorn covu.wsgi:application --bind 0.0.0.0:$PORT
```

Update Render configuration to use Docker runtime.

## Next Steps

1. ✅ Update `settings.py` with Render configuration
2. ✅ Add `build.sh`, `gunicorn`, `whitenoise`, `dj-database-url` to your project
3. ✅ Push changes to GitHub
4. ✅ Create PostgreSQL database on Render
5. ✅ Create Web Service on Render
6. ✅ Configure environment variables
7. ✅ Deploy and test
8. ⏭️ Set up custom domain (optional)
9. ⏭️ Configure SSL certificate (automatic with custom domain)
10. ⏭️ Set up monitoring and alerts

---

**Support**: Render has excellent documentation at https://render.com/docs
