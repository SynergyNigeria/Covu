# COVU Render Deployment Checklist

## ✅ Files Created/Updated

- [x] `build.sh` - Build script for Render
- [x] `render.yaml` - Infrastructure as code (optional)
- [x] `requirements.txt` - Added gunicorn, whitenoise, dj-database-url
- [x] `settings.py` - Updated for Render (DATABASE_URL, WhiteNoise, ALLOWED_HOSTS)
- [x] `RENDER-DEPLOYMENT.md` - Complete deployment guide

## 📋 Quick Deployment Steps

### 1. Push to GitHub

```bash
git add .
git commit -m "Configure for Render deployment"
git push origin master
```

### 2. Create Render Account

- Go to https://render.com and sign up
- Connect your GitHub account

### 3. Create PostgreSQL Database

- Dashboard → New + → PostgreSQL
- Name: `covu-db`
- Region: `Frankfurt` (or closest to users)
- Plan: `Free` (testing) or `Starter` (production)
- Click "Create Database"
- ⏱️ Wait ~2 minutes for provisioning

### 4. Create Web Service

- Dashboard → New + → Web Service
- Select your GitHub repo: `Covu`
- Configure:
  - **Name**: `covu-backend`
  - **Region**: `Frankfurt` (same as database)
  - **Branch**: `master`
  - **Root Directory**: `Backend` (if Django is in subfolder, otherwise leave blank)
  - **Runtime**: `Python 3`
  - **Build Command**: `./build.sh`
  - **Start Command**: `gunicorn covu.wsgi:application --bind 0.0.0.0:$PORT`
  - **Plan**: `Free` (testing) or `Starter` (production $7/month)

### 5. Add Environment Variables

Click "Advanced" and add these (click "Add Environment Variable" for each):

```
SECRET_KEY = [Click "Generate" button]
DEBUG = False
PYTHON_VERSION = 3.11
DATABASE_URL = [Select from database: covu-db]
ALLOWED_HOSTS = .onrender.com

# Paystack (Use your actual keys from Paystack dashboard)
PAYSTACK_SECRET_KEY = sk_live_your_secret_key_here
PAYSTACK_PUBLIC_KEY = pk_live_your_public_key_here
PAYSTACK_WEBHOOK_SECRET = [Get from Paystack dashboard]

# Email
EMAIL_BACKEND = covu.email_backend.CustomEmailBackend
EMAIL_HOST = smtp.zoho.com
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = covumarket@covumarket.com
EMAIL_HOST_PASSWORD = 1998Runs.
DEFAULT_FROM_EMAIL = COVU Marketplace <covumarket@covumarket.com>

# Cloudinary
CLOUDINARY_CLOUD_NAME = dpmxcjkfl
CLOUDINARY_API_KEY = 126559825358577
CLOUDINARY_API_SECRET = PCPdR7La2s_H0A3bfTnOZNFUH44

# Sentry
SENTRY_DSN = https://5c8935e3785f8163f193f27406fde70b@o4510223879110656.ingest.de.sentry.io/4510223884877904

# CORS - Update with actual frontend URL after deployment
CORS_ALLOWED_ORIGINS = https://your-frontend.onrender.com
FRONTEND_URL = https://your-frontend.onrender.com
```

### 6. Deploy

- Click "Create Web Service"
- ⏱️ Wait ~5-10 minutes for first deployment
- Watch the logs for any errors
- Your API will be live at: `https://covu-backend.onrender.com`

### 7. Create Superuser

After deployment succeeds:

- Go to your service dashboard
- Click "Shell" tab
- Run:
  ```bash
  python manage.py createsuperuser
  ```

### 8. Test API

- Visit: `https://covu-backend.onrender.com/api/`
- Should see DRF browsable API
- Admin panel: `https://covu-backend.onrender.com/admin/`

### 9. Configure Paystack Webhook

- Get your webhook URL: `https://covu-backend.onrender.com/api/wallet/paystack-webhook/`
- Go to Paystack Dashboard → Settings → API Keys & Webhooks
- Add webhook URL
- Copy webhook secret → Add to Render environment variables
- Redeploy service for changes to take effect

### 10. Deploy Frontend

#### Option A: Deploy to Render (Static Site)

- Dashboard → New + → Static Site
- Select your GitHub repo
- Configure:
  - **Name**: `covu-frontend`
  - **Branch**: `master`
  - **Root Directory**: `frontend`
  - **Build Command**: (leave empty)
  - **Publish Directory**: `.`
- Click "Create Static Site"
- Frontend URL: `https://covu-frontend.onrender.com`

#### Option B: Deploy to Netlify/Vercel

- Follow their deployment guides
- Update CORS settings with the frontend URL

### 11. Update Frontend API Config

Edit `frontend/assets/js/config.js`:

```javascript
const API_CONFIG = {
  BASE_URL: "https://covu-backend.onrender.com/api",
  // ... rest remains the same
};
```

### 12. Update Backend CORS

In Render dashboard, update environment variable:

```
CORS_ALLOWED_ORIGINS = https://covu-frontend.onrender.com
FRONTEND_URL = https://covu-frontend.onrender.com
```

Click "Manual Deploy" → "Clear build cache & deploy" for changes to take effect

## ⚠️ Important Notes

### Free Tier Limitations

1. **Web service spins down after 15 mins of inactivity**

   - First request takes ~30-60 seconds to wake up
   - Use UptimeRobot.com to ping your site every 5 minutes (keeps it awake)
   - Or upgrade to Starter plan ($7/month) for always-on service

2. **PostgreSQL free tier expires after 90 days**

   - Backup your data before expiration
   - Upgrade to Starter plan ($7/month) for production

3. **500 build minutes/month on free tier**
   - Usually sufficient for small projects

### Production Recommendations

- Upgrade to Starter plan ($7/month each for web + database = $14/month)
- Enable automatic daily database backups
- Set up custom domain (free SSL included)
- Monitor with Sentry (already configured)

### Database Backups

- Go to database dashboard → Backups tab
- Click "Create Backup" for manual backup
- Download backup SQL file for safekeeping
- Schedule automatic backups (Starter plan only)

### Monitoring

- View logs: Service dashboard → Logs tab
- Set up alerts: Settings → Notifications
- Sentry for error tracking (already configured)

## 🚀 Going Live Checklist

Before announcing to users:

- [ ] Test all API endpoints
- [ ] Test user registration and login
- [ ] Test store creation
- [ ] Test product listing
- [ ] Test wallet deposit (with real Paystack payment)
- [ ] Test wallet withdrawal (with real bank account)
- [ ] Test order placement
- [ ] Test email notifications
- [ ] Verify Paystack webhook is working
- [ ] Set up database backups
- [ ] Configure custom domain (optional)
- [ ] Update all URLs in frontend
- [ ] Update CORS settings
- [ ] Test on mobile devices
- [ ] Set DEBUG=False
- [ ] Change SECRET_KEY to secure random value

## 📊 Cost Summary

### Free (Testing - 90 days):

- Backend: Free
- Database: Free (90 days)
- **Total: $0/month**

### Production (Recommended):

- Backend: Starter ($7/month)
- Database: Starter ($7/month)
- **Total: $14/month**

### Scale-Up (If needed):

- Redis: Starter ($7/month)
- CDN: Cloudflare (Free)
- Custom domain: $10-15/year
- **Total: ~$21/month + domain**

## 🆘 Troubleshooting

### Build fails

- Check `build.sh` has correct permissions
- Verify all dependencies in `requirements.txt` are valid
- Check Python version matches (3.11)
- Review logs for specific error messages

### Database connection error

- Verify `DATABASE_URL` environment variable is set
- Check database is in same region as web service
- Ensure database is not suspended (free tier after 90 days)

### Static files not loading

- Run in Render Shell: `python manage.py collectstatic --no-input`
- Verify WhiteNoise is in MIDDLEWARE
- Check STATIC_ROOT and STATIC_URL in settings

### CORS errors

- Update `CORS_ALLOWED_ORIGINS` with exact frontend URL
- Include protocol: `https://` not just domain
- Multiple origins: comma-separated, no spaces
- Redeploy after changing environment variables

### Site is slow/not responding

- Free tier: Service is waking up (wait 30-60 seconds)
- Solution: Upgrade to Starter plan or use UptimeRobot

## 📚 Resources

- Render Docs: https://render.com/docs
- Django Deployment: https://docs.djangoproject.com/en/4.2/howto/deployment/
- WhiteNoise: http://whitenoise.evans.io/
- Gunicorn: https://docs.gunicorn.org/

## 🎉 Success!

Once deployed:

1. Your API is live at: `https://covu-backend.onrender.com`
2. Admin panel: `https://covu-backend.onrender.com/admin/`
3. API docs: `https://covu-backend.onrender.com/api/schema/swagger-ui/`
4. Frontend: `https://covu-frontend.onrender.com`

**Share your live site and start accepting real transactions!** 🚀
