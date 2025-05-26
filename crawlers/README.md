# Distributed Web Crawler Architecture

This module implements a distributed web crawler system designed for global scale news collection. The architecture follows microservices patterns with Docker containerization and Kafka-based event streaming.

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Crawler        │    │  Site Manager   │    │  URL Scheduler  │
│  Registry       │    │  Service        │    │  Service        │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  News Crawler   │    │  Generic        │    │  Monitoring     │
│  Instance 1     │    │  Crawler        │    │  Service        │
│                 │    │  Instance N     │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │     Kafka       │
                    │   (External)    │
                    │                 │
                    └─────────────────┘
```

## Services

### Core Services
- **Crawler Registry**: Manages crawler instances and their assignments
- **Site Manager**: Handles site configurations and policies
- **URL Scheduler**: Manages URL frontier and scheduling
- **Monitoring**: Collects metrics and health status

### Crawler Instances
- **News Crawler**: Specialized for news sites with content extraction
- **Generic Crawler**: General purpose web crawler
- **Custom Crawlers**: Site-specific implementations

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- At least 4GB RAM available
- Ports 6379, 8080-8083, 9092, 2181, 5432 available

### 🚀 Production Setup (Recommended)

1. **Run the setup script**:
   ```bash
   cd crawlers
   ./scripts/setup.sh
   ```

2. **Start the infrastructure** (Kafka, PostgreSQL, Zookeeper):
   ```bash
   # From project root
   docker-compose -f docker-compose.global.yaml up -d
   ```

3. **Start crawler services**:
   ```bash
   cd crawlers
   docker-compose up -d
   ```

4. **Register sites and start crawling**:
   ```bash
   ./scripts/register-sites.sh
   ./scripts/start-crawling.sh
   ```

### 🛠️ Manual Setup (Development)

1. **Start infrastructure**:
   ```bash
   docker-compose -f docker-compose.global.yaml up -d
   ```

2. **Build and start crawlers**:
   ```bash
   cd crawlers
   docker-compose up -d --build
   ```

3. **Wait for services to be ready** (check health):
   ```bash
   curl http://localhost:8080/health  # Registry
   curl http://localhost:8081/health  # Site Manager
   curl http://localhost:8082/health  # Scheduler
   curl http://localhost:8083/health  # Monitoring
   ```

4. **Register a site**:
   ```bash
   curl -X POST http://localhost:8081/sites \
     -H "Content-Type: application/json" \
     -d @config/sites/chile_news.json
   ```

5. **Start crawling**:
   ```bash
   curl -X POST http://localhost:8080/crawlers/start
   ```

## Configuration

Site configurations are stored in `config/sites/` directory. Each site defines:
- Domain and allowed URLs
- Content extraction selectors
- Rate limiting and politeness policies
- Priority and scheduling preferences

## Monitoring

- **Health checks**: `http://localhost:8083/health`
- **Metrics**: `http://localhost:8083/metrics`
- **Crawler status**: `http://localhost:8080/status`

## Development

### 🔧 Local Development Commands

**Quick development setup (recommended):**
```bash
cd crawlers
./scripts/dev.sh start    # Start everything
./scripts/dev.sh status   # Check status
./scripts/dev.sh monitor  # Advanced monitoring dashboard
./scripts/dev.sh logs news-crawler-1  # View logs
./scripts/dev.sh stop     # Stop everything
```

**Manual commands:**

**Start infrastructure only:**
```bash
docker-compose -f docker-compose.global.yaml up -d
```

**Build and start all services:**
```bash
cd crawlers
docker-compose up -d --build
```

**View logs:**
```bash
docker-compose logs -f crawler-registry
docker-compose logs -f news-crawler-1
docker-compose logs -f site-manager
```

**Stop all services:**
```bash
docker-compose down
docker-compose -f ../docker-compose.global.yaml down
```

**Restart a specific service:**
```bash
docker-compose restart news-crawler-1
```

**Check service status:**
```bash
docker-compose ps
curl http://localhost:8080/health
curl http://localhost:8081/health
curl http://localhost:8082/health
curl http://localhost:8083/health
```

### Adding a New Site
1. Create configuration in `config/sites/`
2. Register via Site Manager API
3. Crawler will automatically pick up new sites

### Custom Crawler Implementation
1. Extend `BaseCrawler` class
2. Implement required methods
3. Add to docker-compose configuration

## Testing

Run automated tests to verify system functionality:

```bash
./scripts/test.sh           # Run all tests
./scripts/test.sh health    # Test service health only
./scripts/test.sh api       # Test API endpoints
./scripts/test.sh docker    # Test Docker services
```

## API Documentation

- **Crawler Registry**: `http://localhost:8080/docs`
- **Site Manager**: `http://localhost:8081/docs`
- **URL Scheduler**: `http://localhost:8082/docs`
- **Monitoring**: `http://localhost:8083/docs` 