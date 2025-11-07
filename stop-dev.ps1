# COVU Development Shutdown Script
# This script stops all development services

Write-Host "Stopping COVU Development Environment..." -ForegroundColor Yellow

# Stop Redis
Write-Host ""
Write-Host "Stopping Redis..." -ForegroundColor Cyan
docker-compose stop

Write-Host "Redis stopped" -ForegroundColor Green
Write-Host ""
Write-Host "Note: Stop Django and Celery manually by pressing Ctrl+C in their terminals" -ForegroundColor Yellow
Write-Host "To remove Redis container: docker-compose down" -ForegroundColor Gray
Write-Host "To remove Redis data: docker-compose down -v" -ForegroundColor Gray
Write-Host ""
