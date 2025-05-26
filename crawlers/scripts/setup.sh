#!/bin/bash

# OpenMedia Crawler Setup Script
# This script sets up the crawler environment for production

set -e

echo "🚀 Setting up OpenMedia Crawler Environment..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs
mkdir -p data/redis
mkdir -p config/sites

# Set proper permissions
chmod +x scripts/*.sh

# Build Docker images
echo "🔨 Building Docker images..."
docker-compose build

echo "✅ Setup complete!"
echo ""
echo "🎯 Quick Start Options:"
echo ""
echo "🚀 Production Setup (Recommended):"
echo "  ./scripts/dev.sh start     # Start everything automatically"
echo ""
echo "🛠️ Manual Setup:"
echo "  1. Start infrastructure: docker-compose -f ../docker-compose.global.yaml up -d"
echo "  2. Start crawlers: docker-compose up -d"
echo "  3. Register sites: ./scripts/register-sites.sh"
echo "  4. Start crawling: ./scripts/start-crawling.sh"
echo ""
echo "📊 Monitoring:"
echo "  ./scripts/monitor.sh        # System status"
echo "  ./scripts/test.sh           # Run tests" 