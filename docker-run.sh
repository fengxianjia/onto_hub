#!/bin/bash

# OntoHub Docker Run Script
VERSION=${1:-latest}
echo "--- Starting OntoHub Services (Version: $VERSION) ---"

# Check if containers are already running and stop them
echo "Cleaning up old containers..."
export VERSION=$VERSION
docker-compose down

# Start services in detached mode
echo "Starting services in background..."
export VERSION=$VERSION
docker-compose up -d

# Try to get the IP address (Linux/macOS)
if command -v hostname >/dev/null 2>&1; then
    IP=$(hostname -I | awk '{print $1}')
elif command -v ifconfig >/dev/null 2>&1; then
    IP=$(ifconfig | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1' | awk '{print $2}' | head -n 1)
fi

echo "--- Success ---"
echo "OntoHub is now running!"
echo "  Local:   http://localhost:8004"
[ -n "$IP" ] && echo "  Network: http://$IP:8004"
echo ""
echo "To view logs, use: docker-compose logs -f"
