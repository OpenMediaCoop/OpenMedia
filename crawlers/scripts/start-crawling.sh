#!/bin/bash

# Start the crawling process

set -e

REGISTRY_URL="http://localhost:8080"

echo "🕷️ Starting crawling process..."

# Wait for Crawler Registry to be ready
echo "⏳ Waiting for Crawler Registry to be ready..."
timeout 60 bash -c 'until curl -f $0/health &>/dev/null; do sleep 2; done' $REGISTRY_URL

# Start crawler containers
echo "🚀 Starting crawler instances..."
docker-compose up -d news-crawler-1 news-crawler-2 generic-crawler

# Wait a moment for crawlers to start
echo "⏳ Waiting for crawlers to initialize..."
sleep 10

# Check if crawlers registered successfully
echo "📋 Checking registered crawlers..."
response=$(curl -s "$REGISTRY_URL/crawlers")

if [ $? -eq 0 ]; then
    echo "✅ Crawlers started successfully!"
    echo "$response" | jq '.' 2>/dev/null || echo "$response"
else
    echo "❌ Failed to check crawler status"
    exit 1
fi

echo ""
echo "📊 Monitor crawling status:"
echo "  - Registry: curl $REGISTRY_URL/status"
echo "  - Health: curl $REGISTRY_URL/health"
echo "  - Metrics: curl http://localhost:8083/metrics" 