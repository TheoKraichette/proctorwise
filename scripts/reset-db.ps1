# ==============================================================================
# ProctorWise - Reset des bases de données (PowerShell)
# ==============================================================================

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Set-Location $ProjectRoot

Write-Host "ATTENTION: Ceci va supprimer toutes les donnees!" -ForegroundColor Red
$confirm = Read-Host "Tapez 'oui' pour confirmer"

if ($confirm -ne "oui") {
    Write-Host "Operation annulee." -ForegroundColor Yellow
    exit 0
}

Write-Host "Arret des conteneurs..." -ForegroundColor Yellow
docker compose -f docker-compose.dev.yml down -v

Write-Host "Suppression des volumes..." -ForegroundColor Yellow
docker volume rm proctorwise_mariadb_dev_data 2>$null

Write-Host "Redemarrage..." -ForegroundColor Yellow
& "$ScriptDir\start-dev.ps1"

Write-Host "Reset termine!" -ForegroundColor Green
