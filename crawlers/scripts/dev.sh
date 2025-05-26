#!/bin/bash

# Development helper script for OpenMedia Crawlers

set -e

COMMAND=${1:-help}

case $COMMAND in
    "start")
        echo "🚀 Starting development environment..."
        echo "1. Starting infrastructure..."
        docker-compose -f ../docker-compose.global.yaml up -d
        
        echo "2. Building and starting crawlers..."
        docker-compose up -d --build
        
        echo "3. Waiting for services to be ready..."
        sleep 10
        
        echo "4. Registering sites..."
        ./scripts/register-sites.sh
        
        echo "5. Starting crawling..."
        ./scripts/start-crawling.sh
        
        echo "✅ Development environment ready!"
        ;;
        
    "stop")
        echo "🛑 Stopping development environment..."
        docker-compose down
        docker-compose -f ../docker-compose.global.yaml down
        echo "✅ Environment stopped!"
        ;;
        
    "restart")
        echo "🔄 Restarting development environment..."
        $0 stop
        sleep 2
        $0 start
        ;;
        
    "logs")
        SERVICE=${2:-""}
        if [ -z "$SERVICE" ]; then
            echo "📋 Available services:"
            docker-compose ps --services
            echo ""
            echo "Usage: $0 logs <service-name>"
            echo "Example: $0 logs news-crawler-1"
        else
            docker-compose logs -f $SERVICE
        fi
        ;;
        
    "status")
        echo "📊 Service Status:"
        ./scripts/monitor.sh status
        ;;
        
    "build")
        echo "🔨 Building Docker images..."
        docker-compose build
        echo "✅ Build complete!"
        ;;
        
    "clean")
        echo "🧹 Cleaning up..."
        docker-compose down -v
        docker-compose -f ../docker-compose.global.yaml down -v
        docker system prune -f
        echo "✅ Cleanup complete!"
        ;;
        
    "monitor")
        ./scripts/monitor.sh ${2:-status}
        ;;
        
    "help"|*)
        echo "🕷️ OpenMedia Crawler Development Helper"
        echo ""
        echo "Usage: $0 <command>"
        echo ""
        echo "Commands:"
        echo "  start    - Start the complete development environment"
        echo "  stop     - Stop all services"
        echo "  restart  - Restart the environment"
        echo "  logs     - View logs for a specific service"
        echo "  status   - Check service status and health"
        echo "  monitor  - Advanced monitoring dashboard"
        echo "  build    - Build Docker images"
        echo "  clean    - Clean up containers and volumes"
        echo "  help     - Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0 start"
        echo "  $0 logs news-crawler-1"
        echo "  $0 status"
        ;;
esac 