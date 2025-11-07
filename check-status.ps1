# COVU System Status Checker
# Run this anytime to check if everything is working

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "     COVU System Status Check" -ForegroundColor White
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

# Check Docker
Write-Host "`n🐳 Docker:" -ForegroundColor Yellow -NoNewline
$dockerStatus = docker info 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host " ✅ Running" -ForegroundColor Green
}
else {
    Write-Host " ❌ Not Running" -ForegroundColor Red
    Write-Host "   → Start Docker Desktop" -ForegroundColor Gray
}

# Check Redis Container
Write-Host "📦 Redis Container:" -ForegroundColor Yellow -NoNewline
$redisContainer = docker ps --filter "name=covu-redis" --format "{{.Status}}" 2>&1
if ($redisContainer -and $LASTEXITCODE -eq 0) {
    Write-Host " ✅ $redisContainer" -ForegroundColor Green
}
else {
    Write-Host " ❌ Not Running" -ForegroundColor Red
    Write-Host "   → Run: docker-compose up -d" -ForegroundColor Gray
}

# Test Redis Connection
Write-Host "🔌 Redis Connection:" -ForegroundColor Yellow -NoNewline
$redisPing = docker exec covu-redis redis-cli ping 2>&1
if ($redisPing -eq "PONG") {
    Write-Host " ✅ PONG" -ForegroundColor Green
}
else {
    Write-Host " ❌ No Response" -ForegroundColor Red
}

# Check Django (port 8000)
Write-Host "🌐 Django Server:" -ForegroundColor Yellow -NoNewline
$djangoPort = netstat -ano | Select-String ":8000.*LISTENING"
if ($djangoPort) {
    Write-Host " ✅ Running on :8000" -ForegroundColor Green
}
else {
    Write-Host " ❌ Not Running" -ForegroundColor Red
    Write-Host "   → Run: python manage.py runserver" -ForegroundColor Gray
}

# Check if Celery is running (look for process)
Write-Host "⚙️  Celery Worker:" -ForegroundColor Yellow -NoNewline
$celeryProcess = Get-Process | Where-Object { $_.ProcessName -like "*celery*" -or $_.CommandLine -like "*celery*" }
if ($celeryProcess) {
    Write-Host " ✅ Running" -ForegroundColor Green
}
else {
    Write-Host " ❌ Not Running" -ForegroundColor Red
    Write-Host "   → Run: celery -A covu worker --loglevel=info --pool=solo" -ForegroundColor Gray
}

# Check Python packages
Write-Host "`n📦 Python Packages:" -ForegroundColor Cyan
$packages = @("celery", "redis", "certifi", "django", "djangorestframework")
foreach ($pkg in $packages) {
    Write-Host "   $pkg" -ForegroundColor Yellow -NoNewline
    $installed = pip show $pkg 2>&1
    if ($LASTEXITCODE -eq 0) {
        $version = ($installed | Select-String "Version:").ToString().Split(":")[1].Trim()
        Write-Host " ✅ $version" -ForegroundColor Green
    }
    else {
        Write-Host " ❌ Not installed" -ForegroundColor Red
    }
}

# Check .env file
Write-Host "`n⚙️  Configuration:" -ForegroundColor Cyan
if (Test-Path ".env") {
    Write-Host "   .env file ✅" -ForegroundColor Green
    
    # Check critical settings
    $envContent = Get-Content ".env" -Raw
    $criticalSettings = @(
        "EMAIL_HOST",
        "EMAIL_HOST_USER",
        "REDIS_URL"
    )
    
    foreach ($setting in $criticalSettings) {
        if ($envContent -match $setting) {
            Write-Host "   $setting ✅" -ForegroundColor Green
        }
        else {
            Write-Host "   $setting ❌ Missing" -ForegroundColor Red
        }
    }
}
else {
    Write-Host "   .env file ❌ Not found" -ForegroundColor Red
}

# Summary
Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

$dockerOk = $LASTEXITCODE -eq 0
$redisOk = $redisPing -eq "PONG"
$djangoOk = $djangoPort -ne $null
$celeryOk = $celeryProcess -ne $null

if ($dockerOk -and $redisOk -and $djangoOk -and $celeryOk) {
    Write-Host "     ✅ All Systems Operational!" -ForegroundColor Green
    Write-Host "     Ready to send emails! 🚀" -ForegroundColor White
}
else {
    Write-Host "     ⚠️  Some Services Need Attention" -ForegroundColor Yellow
    Write-Host "`nQuick Fix:" -ForegroundColor Cyan
    Write-Host "   Run: .\start-dev.ps1" -ForegroundColor White
}

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n" -ForegroundColor Cyan
