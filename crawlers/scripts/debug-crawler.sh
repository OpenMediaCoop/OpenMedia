#!/bin/bash

# Script para debugging del crawler

echo "🔍 Debugging OpenMedia Crawler..."
echo "================================"

# Check scheduler URLs
echo ""
echo "📋 Checking URL Scheduler:"
echo "Queue size:"
curl -s http://localhost:8082/queue/size | jq '.' || echo "Failed to get queue size"

echo ""
echo "Scheduler stats:"
curl -s http://localhost:8082/stats | jq '.' || echo "Failed to get stats"

# Check registered crawlers
echo ""
echo "🕷️ Checking Registered Crawlers:"
curl -s http://localhost:8080/status | jq '.crawlers' || echo "Failed to get crawler status"

# Check loaded sites
echo ""
echo "🌐 Checking Loaded Sites:"
curl -s http://localhost:8081/sites | jq '.[].domain' || echo "Failed to get sites"

echo ""
echo "Site count:"
curl -s http://localhost:8081/sites | jq 'length' || echo "Failed to count sites"

# Add some test URLs to the queue
echo ""
echo "➕ Adding test URLs to queue..."

# Add a URL for each configured site
sites=$(curl -s http://localhost:8081/sites)
if [ $? -eq 0 ]; then
    echo "$sites" | jq -c '.[]' | while read site; do
        domain=$(echo "$site" | jq -r '.domain')
        site_id=$(echo "$site" | jq -r '.site_id')
        base_url=$(echo "$site" | jq -r '.base_urls[0]')
        
        if [ "$base_url" != "null" ] && [ "$base_url" != "" ]; then
            echo "Adding URL for $domain: $base_url"
            curl -s -X POST http://localhost:8082/urls \
                -H "Content-Type: application/json" \
                -d "{\"url\": \"$base_url\", \"site_id\": \"$site_id\", \"priority\": 1}" \
                | jq '.' || echo "Failed to add URL"
        fi
    done
else
    echo "Failed to get sites"
fi

# Check queue again
echo ""
echo "📊 Queue status after adding URLs:"
curl -s http://localhost:8082/queue/size | jq '.' || echo "Failed to get queue size"

# Check crawler logs with more context
echo ""
echo "📝 Recent crawler logs:"
docker-compose logs --tail=20 news-crawler-1 | grep -E "(Got URL|No URLs|Processing|Failed|Error|sent to Kafka)"

echo ""
echo "✅ Debug complete!" 