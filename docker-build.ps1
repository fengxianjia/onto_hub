# OntoHub Docker Build Script (Windows)
$VERSION = Get-Date -Format "yyyyMMdd"
$env:VERSION = $VERSION
Write-Host "--- Starting OntoHub Docker Build (Version: $VERSION) ---" -ForegroundColor Cyan

# Step 1: Build Backend
Write-Host "Building Backend image..."
docker-compose build backend

# Step 2: Build Frontend
Write-Host "Building Frontend image..."
docker-compose build frontend

Write-Host "--- Build Complete ---" -ForegroundColor Green
Write-Host "You can now start the services using .\docker-run.ps1"
