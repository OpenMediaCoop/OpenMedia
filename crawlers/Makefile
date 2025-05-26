# OpenMedia News Monitor Makefile

.PHONY: help install run test clean

# Default target
help:
	@echo "🚀 OpenMedia News Monitor - Comandos disponibles:"
	@echo ""
	@echo "  make install    - Instalar dependencias"
	@echo "  make run        - Ejecutar el monitor"
	@echo "  make test       - Probar el monitor (sin Kafka)"
	@echo "  make clean      - Limpiar archivos temporales"
	@echo ""

# Instalar dependencias
install:
	@echo "📦 Instalando dependencias..."
	@pip install -r requirements.txt
	@echo "✅ Dependencias instaladas"

# Ejecutar el monitor
run:
	@echo "🚀 Ejecutando News Monitor..."
	@python run_monitor.py

# Probar sin Kafka
test:
	@echo "🧪 Probando monitor (sin Kafka)..."
	@python -c "from crawlers.news_monitor import NewsMonitor; import asyncio; asyncio.run(NewsMonitor(enable_kafka=False).monitor_site('emol', NewsMonitor()._load_site_configs()['emol']))"

# Limpiar archivos temporales
clean:
	@echo "🧹 Limpiando archivos temporales..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Limpieza completada"

# Setup completo
setup: install
	@echo "⚙️ Configurando entorno..."
	@cp env.example .env 2>/dev/null || true
	@echo "✅ Setup completado"
	@echo ""
	@echo "🎯 Para ejecutar: make run" 