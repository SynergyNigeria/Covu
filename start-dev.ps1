# COVU Development Startup Script
# This script starts Redis, Django, and Celery for local development

Write-Host "Starting COVU Development Environment..." -ForegroundColor Green

# Check if Docker is running
$dockerStatus = docker info 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Start Redis
Write-Host "`nStarting Redis..." -ForegroundColor Cyan
docker-compose up -d

# Wait for Redis to be ready
Write-Host "Waiting for Redis to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# Test Redis connection
$redisTest = docker exec covu-redis redis-cli ping 2>&1
if ($redisTest -eq "PONG") {
    Write-Host "Redis is running!" -ForegroundColor Green
}
else {
    Write-Host "Redis failed to start" -ForegroundColor Red
    exit 1
}

# Start Django in new terminal
Write-Host "`nStarting Django server..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Write-Host 'Django Server' -ForegroundColor Green; python manage.py runserver"

# Wait a moment
Start-Sleep -Seconds 2

# Start Celery in new terminal
Write-Host "Starting Celery worker..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Write-Host 'Celery Worker' -ForegroundColor Yellow; celery -A covu worker --loglevel=info --pool=solo"

Write-Host "`nAll services started!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Gray
Write-Host "Django:  http://localhost:8000" -ForegroundColor White
Write-Host "Redis:   localhost:6379" -ForegroundColor White
Write-Host "Celery:  Running in background" -ForegroundColor White
Write-Host "==========================================" -ForegroundColor Gray
Write-Host ""
Write-Host "Press Ctrl+C in each terminal to stop services" -ForegroundColor Yellow
Write-Host "Run docker-compose down to stop Redis" -ForegroundColor Yellow
Write-Host ""
