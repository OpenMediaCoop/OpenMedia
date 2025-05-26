# 🚀 Quick Start - OpenMedia News Monitor

## ¡En 30 segundos!

```bash
# 1. Clonar e instalar
git clone <repo>
cd crawlers
pip install -r requirements.txt

# 2. ¡Ejecutar!
python run_monitor.py
```

## ¿Qué verás?

```
🚀 OpenMedia News Monitor
==================================================
📰 Monitoreando sitios de noticias chilenos...
⏹️  Presiona Ctrl+C para detener

2025-05-26 19:07:28 [info] Monitoring site site_id=emol url=https://www.emol.com/noticias/
2025-05-26 19:07:28 [info] Found articles count=14 site_id=emol
2025-05-26 19:07:28 [info] Processed article title='Título del artículo...' url=https://...
```

## Comandos útiles

```bash
# Instalar dependencias
make install

# Ejecutar monitor
make run

# Probar sin Kafka
make test

# Limpiar archivos temporales
make clean
```

## Configuración (opcional)

```bash
# Copiar configuración
cp env.example .env

# Editar variables
KAFKA_ENABLED=false          # Deshabilitar Kafka
LOG_LEVEL=DEBUG             # Más logs
MONITOR_INTERVAL=30         # Escanear cada 30 segundos
```

## Agregar sitios

Edita `crawlers/news_monitor.py` en el método `_load_site_configs()`:

```python
'nuevo_sitio': {
    'name': 'Nuevo Sitio',
    'domain': 'nuevositio.cl',
    'homepage': 'https://www.nuevositio.cl/',
    'article_pattern': r'/noticias/',
    'selectors': {
        'article_links': 'a[href*="/noticias/"]',
        'title': 'h1',
        'content': '.contenido'
    }
}
```

## ¡Eso es todo!

**Simple, eficaz, sin complejidad innecesaria.** 