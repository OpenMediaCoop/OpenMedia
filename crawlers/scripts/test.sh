#!/bin/bash

# Automated testing script for OpenMedia Crawlers

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Service URLs
REGISTRY_URL="http://localhost:8080"
SITE_MANAGER_URL="http://localhost:8081"
SCHEDULER_URL="http://localhost:8082"
MONITORING_URL="http://localhost:8083"

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TOTAL_TESTS=0

# Function to run a test
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -e "${BLUE}🧪 Testing: $test_name${NC}"
    
    if eval "$test_command" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS: $test_name${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}❌ FAIL: $test_name${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# Function to test service health
test_service_health() {
    local service_name="$1"
    local url="$2"
    
    run_test "$service_name Health Check" "curl -f $url/health"
}

# Function to test API endpoints
test_api_endpoints() {
    echo -e "${YELLOW}🔌 Testing API Endpoints${NC}"
    echo "================================"
    
    # Test Site Manager endpoints
    run_test "Site Manager - List Sites" "curl -f $SITE_MANAGER_URL/sites"
    run_test "Site Manager - Get Stats" "curl -f $SITE_MANAGER_URL/stats"
    
    # Test URL Scheduler endpoints
    run_test "URL Scheduler - Get Queue Size" "curl -f $SCHEDULER_URL/queue/size"
    run_test "URL Scheduler - Get Stats" "curl -f $SCHEDULER_URL/stats"
    
    # Test Crawler Registry endpoints
    run_test "Crawler Registry - Get Status" "curl -f $REGISTRY_URL/status"
    
    echo ""
}

# Function to test site registration
test_site_registration() {
    echo -e "${YELLOW}📝 Testing Site Registration${NC}"
    echo "================================"
    
    # Create a test site configuration
    local test_site='{
        "domain": "test-site.com",
        "name": "Test Site",
        "base_urls": ["https://test-site.com/"],
        "allowed_domains": ["test-site.com"],
        "selectors": {
            "title": "h1::text",
            "content": "div.content p::text"
        },
        "crawl_delay": 1.0,
        "concurrent_requests": 1,
        "rate_limit": 60,
        "priority": 1,
        "enabled": false
    }'
    
    # Test site registration
    local response=$(curl -s -w "%{http_code}" -X POST \
        -H "Content-Type: application/json" \
        -d "$test_site" \
        "$SITE_MANAGER_URL/sites" \
        -o /tmp/test_response.json)
    
    if [ "$response" -eq 200 ] || [ "$response" -eq 201 ]; then
        echo -e "${GREEN}✅ PASS: Site Registration${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        
        # Get the site ID for cleanup
        local site_id=$(jq -r '.site_id' /tmp/test_response.json 2>/dev/null)
        
        # Test site retrieval
        if curl -f "$SITE_MANAGER_URL/sites/$site_id" >/dev/null 2>&1; then
            echo -e "${GREEN}✅ PASS: Site Retrieval${NC}"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            echo -e "${RED}❌ FAIL: Site Retrieval${NC}"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
        
        # Cleanup: Delete test site
        curl -s -X DELETE "$SITE_MANAGER_URL/sites/$site_id" >/dev/null 2>&1
        
    else
        echo -e "${RED}❌ FAIL: Site Registration (HTTP $response)${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    
    TOTAL_TESTS=$((TOTAL_TESTS + 2))
    echo ""
}

# Function to test URL scheduling
test_url_scheduling() {
    echo -e "${YELLOW}📋 Testing URL Scheduling${NC}"
    echo "================================"
    
    # Test adding a URL
    local test_url='{"url": "https://test-site.com/test-page", "priority": 1}'
    local response=$(curl -s -w "%{http_code}" -X POST \
        -H "Content-Type: application/json" \
        -d "$test_url" \
        "$SCHEDULER_URL/urls" \
        -o /tmp/test_response.json)
    
    if [ "$response" -eq 200 ] || [ "$response" -eq 201 ]; then
        echo -e "${GREEN}✅ PASS: URL Addition${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}❌ FAIL: URL Addition (HTTP $response)${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    
    # Test batch URL addition
    local batch_urls='{"urls": ["https://test-site.com/page1", "https://test-site.com/page2"], "priority": 2}'
    response=$(curl -s -w "%{http_code}" -X POST \
        -H "Content-Type: application/json" \
        -d "$batch_urls" \
        "$SCHEDULER_URL/urls/batch" \
        -o /tmp/test_response.json)
    
    if [ "$response" -eq 200 ] || [ "$response" -eq 201 ]; then
        echo -e "${GREEN}✅ PASS: Batch URL Addition${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}❌ FAIL: Batch URL Addition (HTTP $response)${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    
    TOTAL_TESTS=$((TOTAL_TESTS + 2))
    echo ""
}

# Function to test Docker services
test_docker_services() {
    echo -e "${YELLOW}🐳 Testing Docker Services${NC}"
    echo "================================"
    
    # Check if all expected containers are running
    local expected_services=("crawler-registry" "site-manager" "url-scheduler" "crawler-monitoring" "crawler-redis")
    
    for service in "${expected_services[@]}"; do
        if docker ps --format "{{.Names}}" | grep -q "^$service$"; then
            echo -e "${GREEN}✅ PASS: $service container running${NC}"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            echo -e "${RED}❌ FAIL: $service container not running${NC}"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
        TOTAL_TESTS=$((TOTAL_TESTS + 1))
    done
    
    echo ""
}

# Function to test infrastructure
test_infrastructure() {
    echo -e "${YELLOW}🏗️ Testing Infrastructure${NC}"
    echo "================================"
    
    # Check infrastructure containers
    local infra_services=("kafka" "pgvector" "zookeeper")
    
    for service in "${infra_services[@]}"; do
        if docker ps --format "{{.Names}}" | grep -q "$service"; then
            echo -e "${GREEN}✅ PASS: $service infrastructure running${NC}"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            echo -e "${RED}❌ FAIL: $service infrastructure not running${NC}"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
        TOTAL_TESTS=$((TOTAL_TESTS + 1))
    done
    
    echo ""
}

# Function to show test summary
show_test_summary() {
    echo -e "${YELLOW}📊 Test Summary${NC}"
    echo "================================"
    echo "Total Tests: $TOTAL_TESTS"
    echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
    echo -e "Failed: ${RED}$TESTS_FAILED${NC}"
    
    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "${GREEN}🎉 All tests passed!${NC}"
        return 0
    else
        echo -e "${RED}❌ Some tests failed!${NC}"
        return 1
    fi
}

# Main test function
main() {
    local test_type=${1:-all}
    
    echo -e "${YELLOW}🧪 OpenMedia Crawler Test Suite${NC}"
    echo "=================================================="
    echo ""
    
    case $test_type in
        "health")
            echo -e "${YELLOW}🏥 Testing Service Health${NC}"
            echo "================================"
            test_service_health "Crawler Registry" $REGISTRY_URL
            test_service_health "Site Manager" $SITE_MANAGER_URL
            test_service_health "URL Scheduler" $SCHEDULER_URL
            test_service_health "Monitoring Service" $MONITORING_URL
            echo ""
            ;;
            
        "api")
            test_api_endpoints
            ;;
            
        "registration")
            test_site_registration
            ;;
            
        "scheduling")
            test_url_scheduling
            ;;
            
        "docker")
            test_docker_services
            ;;
            
        "infrastructure")
            test_infrastructure
            ;;
            
        "all"|"")
            # Run all tests
            echo -e "${YELLOW}🏥 Testing Service Health${NC}"
            echo "================================"
            test_service_health "Crawler Registry" $REGISTRY_URL
            test_service_health "Site Manager" $SITE_MANAGER_URL
            test_service_health "URL Scheduler" $SCHEDULER_URL
            test_service_health "Monitoring Service" $MONITORING_URL
            echo ""
            
            test_infrastructure
            test_docker_services
            test_api_endpoints
            test_site_registration
            test_url_scheduling
            ;;
            
        "help")
            echo "Usage: $0 <test-type>"
            echo ""
            echo "Test Types:"
            echo "  all           - Run all tests (default)"
            echo "  health        - Test service health endpoints"
            echo "  api           - Test API endpoints"
            echo "  registration  - Test site registration"
            echo "  scheduling    - Test URL scheduling"
            echo "  docker        - Test Docker services"
            echo "  infrastructure- Test infrastructure services"
            echo "  help          - Show this help message"
            echo ""
            return 0
            ;;
            
        *)
            echo "Unknown test type: $test_type"
            echo "Use '$0 help' for available test types"
            return 1
            ;;
    esac
    
    show_test_summary
}

# Run main function with all arguments
main "$@" 