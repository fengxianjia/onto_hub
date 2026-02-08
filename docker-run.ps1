# OntoHub Docker Run Script (Windows)
param (
    [string]$Version = "latest"
)

$env:VERSION = $Version
Write-Host "--- Starting OntoHub Services (Version: $Version) ---" -ForegroundColor Cyan

# Check if containers are already running and stop them
Write-Host "Cleaning up old containers..."
docker-compose down

# Start services in detached mode
Write-Host "Starting services in background..."
docker-compose up -d

# Get the local IP address
$ip = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -match "Ethernet|Wi-Fi|WLAN" -and $_.IPAddress -notmatch "^169\." } | Select-Object -First 1).IPAddress

Write-Host "--- Success ---" -ForegroundColor Green
Write-Host "OntoHub is now running!"
Write-Host "  Local:   http://localhost:8004"
if ($ip) {
    Write-Host "  Network: http://$($ip):8004"
}
Write-Host ""
Write-Host "To view logs, use: docker-compose logs -f"
