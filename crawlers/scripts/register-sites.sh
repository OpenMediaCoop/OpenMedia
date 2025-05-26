#!/bin/bash

# Register site configurations with the Site Manager

set -e

SITE_MANAGER_URL="http://localhost:8081"
CONFIG_DIR="./config/sites"

echo "📝 Registering site configurations..."

# Wait for Site Manager to be ready
echo "⏳ Waiting for Site Manager to be ready..."
timeout 60 bash -c 'until curl -f $0/health &>/dev/null; do sleep 2; done' $SITE_MANAGER_URL

# Register each site configuration using bulk upload
for config_file in $CONFIG_DIR/*.json; do
    if [ -f "$config_file" ]; then
        site_name=$(basename "$config_file" .json)
        echo "📄 Registering sites from $site_name..."
        
        # Use bulk upload endpoint for better efficiency
        response=$(curl -s -w "%{http_code}" -X POST \
            -F "file=@$config_file" \
            "$SITE_MANAGER_URL/sites/bulk" \
            -o /tmp/response.json)
        
        if [ "$response" -eq 200 ] || [ "$response" -eq 201 ]; then
            echo "✅ Successfully registered sites from $site_name"
            # Show summary of registered sites
            jq -r '.[] | "  - \(.site_id): \(.status) - \(.message)"' /tmp/response.json 2>/dev/null || echo "  Response processed successfully"
        else
            echo "❌ Failed to register sites from $site_name (HTTP $response)"
            cat /tmp/response.json
        fi
        echo ""
    fi
done

echo ""
echo "🎉 Site registration complete!"
echo "Check registered sites: curl $SITE_MANAGER_URL/sites" 