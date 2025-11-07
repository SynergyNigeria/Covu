# Test Email System Script
# Run this to verify Celery and email are working

Write-Host "🧪 Testing COVU Email System..." -ForegroundColor Green

# Check Docker
Write-Host "`n1️⃣ Checking Docker..." -ForegroundColor Cyan
$dockerRunning = docker info 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker is not running" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Docker is running" -ForegroundColor Green

# Check Redis
Write-Host "`n2️⃣ Checking Redis..." -ForegroundColor Cyan
$redisStatus = docker ps --filter "name=covu-redis" --format "{{.Status}}"
if (-not $redisStatus) {
    Write-Host "❌ Redis container not found. Run: docker-compose up -d" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Redis container: $redisStatus" -ForegroundColor Green

# Test Redis connection
Write-Host "`n3️⃣ Testing Redis connection..." -ForegroundColor Cyan
$redisPing = docker exec covu-redis redis-cli ping 2>&1
if ($redisPing -eq "PONG") {
    Write-Host "✅ Redis responds: PONG" -ForegroundColor Green
}
else {
    Write-Host "❌ Redis not responding" -ForegroundColor Red
    exit 1
}

# Check Celery (requires Django to be running)
Write-Host "`n4️⃣ Checking Celery tasks..." -ForegroundColor Cyan
Write-Host "Note: This requires Django to be running" -ForegroundColor Yellow

# Create Python test script
$pythonScript = @"
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'covu.settings')
django.setup()

from notifications.tasks import send_email_task

# Try to queue a test email
try:
    result = send_email_task.delay(
        subject='COVU Test Email',
        message='This is a test email from Celery async worker!',
        recipient_list=['test@example.com']
    )
    print(f'✅ Email queued successfully! Task ID: {result.id}')
    print(f'Check Celery worker terminal to see it processing')
except Exception as e:
    print(f'❌ Error queueing email: {e}')
"@

$pythonScript | Out-File -FilePath "test_celery_email.py" -Encoding utf8

Write-Host "Running email queue test..." -ForegroundColor Yellow
python test_celery_email.py

Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host "✨ Test Complete!" -ForegroundColor Green
Write-Host "`nTo send a real email, update the recipient in test_celery_email.py" -ForegroundColor Cyan
Write-Host "Then run: python test_celery_email.py`n" -ForegroundColor Cyan

# Cleanup
Remove-Item "test_celery_email.py" -ErrorAction SilentlyContinue
