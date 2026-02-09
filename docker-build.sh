#!/bin/bash

# OntoHub Docker Build Script
VERSION=$(date +%Y%m%d)
echo "--- Starting OntoHub Docker Build (Version: $VERSION) ---"

# Step 1: Build & Tag Backend
echo "Building Backend image..."
export VERSION=$VERSION
docker-compose build backend

# Step 2: Build & Tag Frontend
echo "Building Frontend image..."
export VERSION=$VERSION
docker-compose build frontend

echo "--- Build Complete ---"
echo "You can now start the services using ./docker-run.sh"
