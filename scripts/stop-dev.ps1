# ==============================================================================
# ProctorWise - Script d'arrêt développement (PowerShell)
# ==============================================================================

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Set-Location $ProjectRoot

Write-Host "Arret de l'infrastructure de developpement..." -ForegroundColor Yellow
docker compose -f docker-compose.dev.yml down

Write-Host "Infrastructure arretee." -ForegroundColor Green
