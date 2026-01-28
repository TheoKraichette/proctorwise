# ==============================================================================
# ProctorWise - Script de test de la stack
# ==============================================================================
# Usage: .\scripts\test-stack.ps1
# ==============================================================================

$ErrorActionPreference = "Continue"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  ProctorWise - Test de la stack" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

$passed = 0
$failed = 0

function Test-Endpoint {
    param (
        [string]$Name,
        [string]$Url
    )

    try {
        $response = Invoke-RestMethod -Uri $Url -Method Get -TimeoutSec 5 -ErrorAction Stop
        Write-Host "[OK] $Name" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "[FAIL] $Name - $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

Write-Host "Test des microservices..." -ForegroundColor Yellow
Write-Host ""

# Test des microservices
$services = @(
    @{ Name = "UserService (8001)"; Url = "http://localhost:8001/health" },
    @{ Name = "ReservationService (8000)"; Url = "http://localhost:8000/health" },
    @{ Name = "MonitoringService (8003)"; Url = "http://localhost:8003/health" },
    @{ Name = "CorrectionService (8004)"; Url = "http://localhost:8004/health" },
    @{ Name = "NotificationService (8005)"; Url = "http://localhost:8005/health" },
    @{ Name = "AnalyticsService (8006)"; Url = "http://localhost:8006/health" }
)

foreach ($service in $services) {
    if (Test-Endpoint -Name $service.Name -Url $service.Url) {
        $passed++
    } else {
        $failed++
    }
}

Write-Host ""
Write-Host "Test des interfaces web..." -ForegroundColor Yellow
Write-Host ""

# Test des interfaces web
$webUIs = @(
    @{ Name = "Kafka UI (8080)"; Url = "http://localhost:8080" },
    @{ Name = "Spark Master (8081)"; Url = "http://localhost:8081" },
    @{ Name = "Airflow (8082)"; Url = "http://localhost:8082/health" },
    @{ Name = "Adminer (8083)"; Url = "http://localhost:8083" },
    @{ Name = "MailHog (8025)"; Url = "http://localhost:8025" },
    @{ Name = "HDFS NameNode (9870)"; Url = "http://localhost:9870" }
)

foreach ($ui in $webUIs) {
    if (Test-Endpoint -Name $ui.Name -Url $ui.Url) {
        $passed++
    } else {
        $failed++
    }
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  Resultats" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  Passes: $passed" -ForegroundColor Green
Write-Host "  Echecs: $failed" -ForegroundColor $(if ($failed -gt 0) { "Red" } else { "Green" })
Write-Host ""

if ($failed -eq 0) {
    Write-Host "Tous les tests sont passes!" -ForegroundColor Green
} else {
    Write-Host "Certains services ne sont pas prets." -ForegroundColor Yellow
    Write-Host "Verifiez les logs avec: docker compose logs -f" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  URLs des services" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Microservices:" -ForegroundColor Yellow
Write-Host "  UserService:         http://localhost:8001/docs"
Write-Host "  ReservationService:  http://localhost:8000/docs"
Write-Host "  MonitoringService:   http://localhost:8003/docs"
Write-Host "  CorrectionService:   http://localhost:8004/docs"
Write-Host "  NotificationService: http://localhost:8005/docs"
Write-Host "  AnalyticsService:    http://localhost:8006/docs"
Write-Host ""
Write-Host "Interfaces:" -ForegroundColor Yellow
Write-Host "  Kafka UI:    http://localhost:8080"
Write-Host "  Spark:       http://localhost:8081"
Write-Host "  Airflow:     http://localhost:8082 (admin/admin)"
Write-Host "  Adminer:     http://localhost:8083 (proctorwise/proctorwise_secret)"
Write-Host "  MailHog:     http://localhost:8025"
Write-Host "  HDFS:        http://localhost:9870"
Write-Host ""
