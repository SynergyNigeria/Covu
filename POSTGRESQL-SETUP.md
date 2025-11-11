# PostgreSQL Setup Guide for COVU Production

## Prerequisites

- PostgreSQL 14+ installed on your production server
- Admin access to PostgreSQL

## Step 1: Install PostgreSQL

### On Ubuntu/Debian Server:

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### On Windows (Local Testing):

Download and install from: https://www.postgresql.org/download/windows/

## Step 2: Create Database and User

```bash
# Switch to postgres user
sudo -u postgres psql

# Inside PostgreSQL shell, run these commands:
CREATE DATABASE covu_db;
CREATE USER covu_user WITH PASSWORD 'your_strong_password_here';

# Grant privileges
ALTER ROLE covu_user SET client_encoding TO 'utf8';
ALTER ROLE covu_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE covu_user SET timezone TO 'Africa/Lagos';
GRANT ALL PRIVILEGES ON DATABASE covu_db TO covu_user;

# For PostgreSQL 15+, also grant schema privileges
\c covu_db
GRANT ALL ON SCHEMA public TO covu_user;

# Exit
\q
```

## Step 3: Update .env File

Update your `.env` file with PostgreSQL credentials:

```env
# Database - Enable PostgreSQL
USE_POSTGRESQL=True

# PostgreSQL Configuration
POSTGRES_DB=covu_db
POSTGRES_USER=covu_user
POSTGRES_PASSWORD=your_strong_password_here
POSTGRES_HOST=localhost  # or your database server IP
POSTGRES_PORT=5432
```

## Step 4: Install Python PostgreSQL Driver (Already Done)

Your `requirements.txt` already includes `psycopg[binary]==3.2.3`, which is the PostgreSQL adapter for Python.

If you need to reinstall:

```bash
pip install psycopg[binary]==3.2.3
```

## Step 5: Migrate Existing Data (Optional)

If you have existing SQLite data you want to transfer:

### Option A: Using Django dumpdata/loaddata (Recommended)

```bash
# 1. Export data from SQLite
python manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e auth.Permission --indent 2 > data_backup.json

# 2. Switch to PostgreSQL (update .env: USE_POSTGRESQL=True)

# 3. Run migrations
python manage.py migrate

# 4. Load data into PostgreSQL
python manage.py loaddata data_backup.json
```

### Option B: Start Fresh (Clean Database)

```bash
# Just run migrations on PostgreSQL
python manage.py migrate
```

## Step 6: Test Connection

```bash
# Test database connection
python manage.py shell

# Inside shell:
from django.db import connection
cursor = connection.cursor()
cursor.execute("SELECT version();")
print(cursor.fetchone())
# Should print PostgreSQL version
```

## Step 7: Create Superuser (if starting fresh)

```bash
python manage.py createsuperuser
```

## Production Configuration Checklist

### Database Performance

- [x] `CONN_MAX_AGE=600` - Connection pooling enabled
- [ ] Consider using **pgBouncer** for connection pooling in high-traffic scenarios

### Database Backups

```bash
# Manual backup
pg_dump -U covu_user -h localhost covu_db > backup_$(date +%Y%m%d).sql

# Restore from backup
psql -U covu_user -h localhost covu_db < backup_20250111.sql

# Setup automated daily backups (cron job)
0 2 * * * pg_dump -U covu_user -h localhost covu_db | gzip > /backups/covu_$(date +\%Y\%m\%d).sql.gz
```

### Security Best Practices

1. **Strong Password**: Use a strong password for `covu_user`

   ```bash
   # Generate strong password
   openssl rand -base64 32
   ```

2. **Firewall**: Only allow database connections from your app server

   ```bash
   # Edit PostgreSQL config
   sudo nano /etc/postgresql/14/main/pg_hba.conf

   # Add this line (replace with your app server IP)
   host    covu_db    covu_user    YOUR_APP_SERVER_IP/32    md5
   ```

3. **SSL Connection** (Production recommended):
   Update settings.py to require SSL:
   ```python
   "OPTIONS": {
       "sslmode": "require",
   }
   ```

### Monitoring & Maintenance

```bash
# Check database size
SELECT pg_size_pretty(pg_database_size('covu_db'));

# Check table sizes
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

# Vacuum and analyze (optimize database)
VACUUM ANALYZE;
```

## Switching Between SQLite and PostgreSQL

### For Development (SQLite):

```env
USE_POSTGRESQL=False
```

### For Production (PostgreSQL):

```env
USE_POSTGRESQL=True
POSTGRES_DB=covu_db
POSTGRES_USER=covu_user
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=your_server_ip
POSTGRES_PORT=5432
```

## Common Issues & Solutions

### Issue: "Peer authentication failed"

**Solution**: Edit `pg_hba.conf` and change `peer` to `md5`:

```bash
sudo nano /etc/postgresql/14/main/pg_hba.conf
# Change: local all all peer
# To:     local all all md5
sudo systemctl restart postgresql
```

### Issue: "Could not connect to server"

**Solution**: PostgreSQL not accepting remote connections

```bash
sudo nano /etc/postgresql/14/main/postgresql.conf
# Change: listen_addresses = 'localhost'
# To:     listen_addresses = '*'
sudo systemctl restart postgresql
```

### Issue: "Permission denied for schema public"

**Solution**: Grant schema privileges (PostgreSQL 15+)

```sql
\c covu_db
GRANT ALL ON SCHEMA public TO covu_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO covu_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO covu_user;
```

## Performance Tuning for Production

Add to PostgreSQL config (`postgresql.conf`):

```conf
# Memory settings (adjust based on your server RAM)
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
work_mem = 16MB

# Connection settings
max_connections = 100
```

## Deployment Platforms

### Heroku

Heroku automatically provides PostgreSQL. Just add:

```bash
heroku addons:create heroku-postgresql:mini
```

### DigitalOcean

Use Managed PostgreSQL Database:

- Automatic backups
- Connection pooling
- High availability

### AWS RDS

Amazon RDS for PostgreSQL provides enterprise-level database hosting.

### Railway

Provides free PostgreSQL database with simple setup.

## Next Steps

1. ✅ Configure `.env` with PostgreSQL credentials
2. ✅ Run `python manage.py migrate`
3. ✅ Test the connection
4. ⏭️ Set up automated backups
5. ⏭️ Configure monitoring (optional: use pgAdmin or DataGrip)
6. ⏭️ Optimize queries using `django-debug-toolbar` during testing

---

**Note**: Keep SQLite for local development (`USE_POSTGRESQL=False`) and only switch to PostgreSQL for staging/production environments.
