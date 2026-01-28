# ==============================================================================
# ProctorWise - Script de démarrage développement (PowerShell)
# ==============================================================================

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Set-Location $ProjectRoot

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  ProctorWise - Demarrage dev" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Démarrer l'infrastructure avec docker-compose.dev.yml
Write-Host "[1/3] Demarrage de l'infrastructure..." -ForegroundColor Yellow
docker compose -f docker-compose.dev.yml up -d

Write-Host "[2/3] Attente que les services soient prets..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Vérifier que MariaDB est prêt
Write-Host "    - Verification MariaDB..." -ForegroundColor Gray
$maxRetries = 30
$retry = 0
do {
    $retry++
    try {
        $result = docker exec proctorwise-mariadb-dev mysqladmin ping -h localhost -u root -pproctorwise_root_secret 2>$null
        if ($result -match "mysqld is alive") { break }
    } catch {}
    Write-Host "    - MariaDB pas encore pret, attente..." -ForegroundColor Gray
    Start-Sleep -Seconds 2
} while ($retry -lt $maxRetries)
Write-Host "    - MariaDB OK" -ForegroundColor Green

# Vérifier que Kafka est prêt
Write-Host "    - Verification Kafka..." -ForegroundColor Gray
$retry = 0
do {
    $retry++
    try {
        docker exec proctorwise-kafka-dev kafka-broker-api-versions --bootstrap-server localhost:9092 2>$null
        if ($LASTEXITCODE -eq 0) { break }
    } catch {}
    Write-Host "    - Kafka pas encore pret, attente..." -ForegroundColor Gray
    Start-Sleep -Seconds 2
} while ($retry -lt $maxRetries)
Write-Host "    - Kafka OK" -ForegroundColor Green

Write-Host "[3/3] Infrastructure prete!" -ForegroundColor Green
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  Services disponibles:" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  MariaDB:    localhost:3306" -ForegroundColor White
Write-Host "  Kafka:      localhost:9092" -ForegroundColor White
Write-Host "  Kafka UI:   http://localhost:8080" -ForegroundColor White
Write-Host "  MailHog:    http://localhost:8025" -ForegroundColor White
Write-Host "  Adminer:    http://localhost:8083" -ForegroundColor White
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Pour lancer un microservice:" -ForegroundColor Yellow
Write-Host "  cd userservice; uvicorn main:app --reload --port 8001" -ForegroundColor Gray
Write-Host "  cd reservationservice; uvicorn main:app --reload --port 8000" -ForegroundColor Gray
Write-Host "  cd monitoringservice; uvicorn main:app --reload --port 8003" -ForegroundColor Gray
Write-Host "  cd correctionservice; uvicorn main:app --reload --port 8004" -ForegroundColor Gray
Write-Host "  cd notificationservice; uvicorn main:app --reload --port 8005" -ForegroundColor Gray
Write-Host "  cd analyticsservice; uvicorn main:app --reload --port 8006" -ForegroundColor Gray
Write-Host ""
