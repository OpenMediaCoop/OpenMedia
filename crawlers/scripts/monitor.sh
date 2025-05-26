#!/bin/bash

# Advanced monitoring script for OpenMedia Crawlers

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

# Function to check service health
check_service() {
    local service_name=$1
    local url=$2
    local response=$(curl -s -w "%{http_code}" -o /dev/null "$url/health" 2>/dev/null || echo "000")
    
    if [ "$response" -eq 200 ]; then
        echo -e "${GREEN}✅ $service_name${NC}"
        return 0
    else
        echo -e "${RED}❌ $service_name (HTTP $response)${NC}"
        return 1
    fi
}

# Function to get service stats
get_service_stats() {
    local service_name=$1
    local url=$2
    local endpoint=$3
    
    echo -e "${BLUE}📊 $service_name Stats:${NC}"
    local response=$(curl -s "$url$endpoint" 2>/dev/null)
    
    if [ $? -eq 0 ] && [ -n "$response" ]; then
        echo "$response" | jq '.' 2>/dev/null || echo "$response"
    else
        echo -e "${RED}  Unable to fetch stats${NC}"
    fi
    echo ""
}

# Function to show docker status
show_docker_status() {
    echo -e "${BLUE}🐳 Docker Services Status:${NC}"
    docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "Docker compose not running"
    echo ""
}

# Function to show infrastructure status
show_infrastructure_status() {
    echo -e "${BLUE}🏗️ Infrastructure Status:${NC}"
    
    # Check Kafka
    if docker ps --format "table {{.Names}}" | grep -q kafka; then
        echo -e "${GREEN}✅ Kafka${NC}"
    else
        echo -e "${RED}❌ Kafka${NC}"
    fi
    
    # Check PostgreSQL
    if docker ps --format "table {{.Names}}" | grep -q pgvector; then
        echo -e "${GREEN}✅ PostgreSQL${NC}"
    else
        echo -e "${RED}❌ PostgreSQL${NC}"
    fi
    
    # Check Zookeeper
    if docker ps --format "table {{.Names}}" | grep -q zookeeper; then
        echo -e "${GREEN}✅ Zookeeper${NC}"
    else
        echo -e "${RED}❌ Zookeeper${NC}"
    fi
    
    # Check Redis
    if docker ps --format "table {{.Names}}" | grep -q crawler-redis; then
        echo -e "${GREEN}✅ Redis${NC}"
    else
        echo -e "${RED}❌ Redis${NC}"
    fi
    echo ""
}

# Function to show crawler instances
show_crawler_instances() {
    echo -e "${BLUE}🕷️ Crawler Instances:${NC}"
    
    # Get crawler status from registry
    local response=$(curl -s "$REGISTRY_URL/status" 2>/dev/null)
    
    if [ $? -eq 0 ] && [ -n "$response" ]; then
        echo "$response" | jq -r '.crawlers[] | "  \(.crawler_id): \(.status) (\(.last_seen))"' 2>/dev/null || echo "  Unable to parse crawler status"
    else
        echo -e "${RED}  Unable to fetch crawler status${NC}"
    fi
    echo ""
}

# Function to show queue status
show_queue_status() {
    echo -e "${BLUE}📋 Queue Status:${NC}"
    
    # Get queue size
    local queue_size=$(curl -s "$SCHEDULER_URL/queue/size" 2>/dev/null | jq -r '.size' 2>/dev/null || echo "N/A")
    echo "  Queue Size: $queue_size"
    
    # Get scheduler stats
    local stats=$(curl -s "$SCHEDULER_URL/stats" 2>/dev/null)
    if [ $? -eq 0 ] && [ -n "$stats" ]; then
        echo "  In Progress: $(echo "$stats" | jq -r '.in_progress_count' 2>/dev/null || echo "N/A")"
        echo "  Failed: $(echo "$stats" | jq -r '.failed_count' 2>/dev/null || echo "N/A")"
    fi
    echo ""
}

# Function to show recent logs
show_recent_logs() {
    local service=$1
    local lines=${2:-10}
    
    echo -e "${BLUE}📝 Recent logs for $service (last $lines lines):${NC}"
    docker-compose logs --tail=$lines $service 2>/dev/null || echo "  Unable to fetch logs for $service"
    echo ""
}

# Main monitoring function
main() {
    local command=${1:-status}
    
    case $command in
        "status"|"")
            clear
            echo -e "${YELLOW}🕷️ OpenMedia Crawler System Monitor${NC}"
            echo "=================================================="
            echo ""
            
            # Check service health
            echo -e "${BLUE}🏥 Service Health:${NC}"
            check_service "Crawler Registry" $REGISTRY_URL
            check_service "Site Manager" $SITE_MANAGER_URL
            check_service "URL Scheduler" $SCHEDULER_URL
            check_service "Monitoring Service" $MONITORING_URL
            echo ""
            
            # Show infrastructure
            show_infrastructure_status
            
            # Show docker status
            show_docker_status
            
            # Show crawler instances
            show_crawler_instances
            
            # Show queue status
            show_queue_status
            ;;
            
        "stats")
            echo -e "${YELLOW}📊 Detailed Service Statistics${NC}"
            echo "=================================================="
            echo ""
            
            get_service_stats "Site Manager" $SITE_MANAGER_URL "/stats"
            get_service_stats "URL Scheduler" $SCHEDULER_URL "/stats"
            get_service_stats "Crawler Registry" $REGISTRY_URL "/status"
            ;;
            
        "logs")
            local service=${2:-""}
            if [ -z "$service" ]; then
                echo "Available services:"
                docker-compose ps --services 2>/dev/null || echo "No services found"
                echo ""
                echo "Usage: $0 logs <service-name> [lines]"
                echo "Example: $0 logs news-crawler-1 20"
            else
                local lines=${3:-20}
                show_recent_logs $service $lines
            fi
            ;;
            
        "watch")
            echo "Starting continuous monitoring (press Ctrl+C to stop)..."
            while true; do
                $0 status
                echo ""
                echo -e "${YELLOW}Refreshing in 10 seconds...${NC}"
                sleep 10
            done
            ;;
            
        "help")
            echo -e "${YELLOW}🕷️ OpenMedia Crawler Monitor${NC}"
            echo ""
            echo "Usage: $0 <command>"
            echo ""
            echo "Commands:"
            echo "  status   - Show overall system status (default)"
            echo "  stats    - Show detailed service statistics"
            echo "  logs     - Show recent logs for a service"
            echo "  watch    - Continuous monitoring mode"
            echo "  help     - Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 status"
            echo "  $0 stats"
            echo "  $0 logs news-crawler-1 50"
            echo "  $0 watch"
            ;;
            
        *)
            echo "Unknown command: $command"
            echo "Use '$0 help' for available commands"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@" 