# OpenMedia Crawlers Makefile

.PHONY: help setup start stop restart status logs test clean build shell validate

# Default target
help:
	@echo "OpenMedia Crawlers - Comandos disponibles:"
	@echo ""
	@echo "  make setup      - Configurar el entorno inicial"
	@echo "  make start      - Iniciar todos los servicios"
	@echo "  make stop       - Detener todos los servicios"
	@echo "  make restart    - Reiniciar todos los servicios"
	@echo "  make status     - Ver estado del sistema"
	@echo "  make logs       - Ver logs de todos los servicios"
	@echo "  make test       - Ejecutar tests"
	@echo "  make clean      - Limpiar contenedores y volúmenes"
	@echo "  make build      - Reconstruir imágenes Docker"
	@echo "  make shell      - Abrir shell en contenedor"
	@echo "  make validate   - Validar configuración del sistema"
	@echo ""
	@echo "Comandos específicos:"
	@echo "  make logs-crawler1  - Logs del crawler 1"
	@echo "  make logs-crawler2  - Logs del crawler 2"
	@echo "  make logs-registry  - Logs del registry"
	@echo "  make test-health    - Solo health checks"
	@echo ""

# Configuración inicial
setup:
	@echo "🚀 Configurando entorno..."
	@chmod +x scripts/*.sh
	@./scripts/setup.sh

# Iniciar servicios
start:
	@echo "🚀 Iniciando servicios..."
	@./scripts/dev.sh start

# Detener servicios
stop:
	@echo "🛑 Deteniendo servicios..."
	@./scripts/dev.sh stop

# Reiniciar servicios
restart:
	@echo "🔄 Reiniciando servicios..."
	@./scripts/dev.sh restart

# Ver estado
status:
	@./scripts/monitor.sh status

# Ver logs
logs:
	@docker-compose logs -f --tail=100

# Logs específicos
logs-crawler1:
	@docker-compose logs -f --tail=100 news-crawler-1

logs-crawler2:
	@docker-compose logs -f --tail=100 news-crawler-2

logs-registry:
	@docker-compose logs -f --tail=100 crawler-registry

logs-scheduler:
	@docker-compose logs -f --tail=100 url-scheduler

logs-site-manager:
	@docker-compose logs -f --tail=100 site-manager

# Ejecutar tests
test:
	@./scripts/test.sh all

test-health:
	@./scripts/test.sh health

test-api:
	@./scripts/test.sh api

# Limpiar
clean:
	@echo "🧹 Limpiando..."
	@./scripts/dev.sh clean

# Construir imágenes
build:
	@echo "🔨 Construyendo imágenes..."
	@docker-compose build

# Shell interactivo
shell:
	@docker-compose exec news-crawler-1 /bin/bash

# Shell en servicio específico
shell-registry:
	@docker-compose exec crawler-registry /bin/bash

shell-scheduler:
	@docker-compose exec url-scheduler /bin/bash

# Monitoreo continuo
watch:
	@./scripts/monitor.sh watch

# Verificar sintaxis de configuración
check-config:
	@echo "🔍 Verificando configuraciones..."
	@python -m json.tool config/sites/chile_news.json > /dev/null && echo "✅ chile_news.json válido" || echo "❌ chile_news.json inválido"

# Ver métricas
metrics:
	@curl -s http://localhost:8083/metrics | jq '.' || echo "❌ Servicio de monitoreo no disponible"

# Registrar sitios
register-sites:
	@./scripts/register-sites.sh

# Estado de la infraestructura
infra-status:
	@echo "🏗️ Estado de la infraestructura:"
	@docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "(kafka|pgvector|zookeeper|redis)"

# Desarrollo local con Python
dev-local:
	@echo "🐍 Configurando entorno Python local..."
	@python -m venv venv || true
	@echo "✅ Activar con: source venv/bin/activate"
	@echo "✅ Instalar deps: pip install -r requirements.txt"

# Validar configuración
validate:
	@chmod +x scripts/validate.sh
	@./scripts/validate.sh

# Debug crawler
debug:
	@chmod +x scripts/debug-crawler.sh
	@./scripts/debug-crawler.sh 