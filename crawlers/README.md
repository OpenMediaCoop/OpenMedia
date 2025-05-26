# OpenMedia News Monitor

Monitor simple y eficaz para sitios de noticias chilenos. **¡Sin complejidad innecesaria!**

## 🚀 Quick Start

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Configurar variables (opcional)
cp env.example .env

# 3. ¡Ejecutar!
python run_monitor.py
```

**¡Eso es todo!** El monitor comenzará a escanear sitios de noticias chilenos automáticamente.

> 💡 **¿Súper apurado?** Ver [`QUICK_START.md`](QUICK_START.md) para setup en 30 segundos.

## 🎯 Filosofía: Simple pero Eficaz

Este proyecto sigue una filosofía de **simplicidad máxima**:

- ✅ **Un solo archivo principal**: `news_monitor.py`
- ✅ **Dependencias mínimas**: Solo 6 librerías esenciales
- ✅ **Sin Docker**: Ejecuta directamente con Python
- ✅ **Sin microservicios**: Una aplicación, un propósito
- ✅ **Sin bases de datos**: Envía directamente a Kafka
- ✅ **Configuración en código**: Fácil de modificar y entender

## 📰 ¿Qué hace?

El News Monitor:

1. **Escanea** las páginas principales de sitios de noticias chilenos
2. **Extrae** enlaces a artículos nuevos
3. **Descarga** el contenido completo de cada artículo
4. **Procesa** y limpia el texto
5. **Envía** todo a Kafka para procesamiento posterior

Todo esto de forma **continua** y **automática**.

## 🌐 Sitios Soportados

| Sitio | URL | Estado |
|-------|-----|--------|
| El Mercurio Online | emol.com | ✅ Activo |
| La Tercera | latercera.com | ✅ Activo |
| BioBio Chile | biobiochile.cl | ✅ Activo |

## 📋 Requisitos

- Python 3.8+
- Kafka (opcional, para envío de datos)
- 512MB RAM
- Conexión a internet

## ⚙️ Configuración

### Variables de Entorno (.env)

```bash
# Kafka (opcional)
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_ENABLED=true

# Logging
LOG_LEVEL=INFO
```

### Agregar un Nuevo Sitio

Edita `news_monitor.py` y agrega la configuración en el método `_load_site_configs()`:

```python
'nuevo_sitio': {
    'name': 'Nuevo Sitio',
    'domain': 'nuevositio.cl',
    'homepage': 'https://www.nuevositio.cl/',
    'article_pattern': r'/noticias/',
    'selectors': {
        'article_links': 'a[href*="/noticias/"]',
        'title': 'h1',
        'content': '.contenido',
        'author': '.autor',
        'date': 'time'
    }
}
```

## 📊 Monitoreo

El monitor incluye logging estructurado que muestra:

- Sitios escaneados
- Artículos encontrados
- Artículos procesados
- Errores y estadísticas

```bash
# Ver logs en tiempo real
python run_monitor.py

# Ejemplo de salida:
2024-01-15 12:30:15 [INFO] Starting news monitor sites=['emol', 'latercera', 'biobio']
2024-01-15 12:30:16 [INFO] Monitoring site site_id=emol url=https://www.emol.com/noticias/
2024-01-15 12:30:17 [INFO] Found articles site_id=emol count=25
2024-01-15 12:30:18 [INFO] Processed article url=https://www.emol.com/... title=Título del artículo
```

## 📨 Formato de Datos

Cada artículo procesado se envía a Kafka con este formato:

```json
{
  "url": "https://www.emol.com/noticias/...",
  "site_id": "emol",
  "site_name": "El Mercurio Online",
  "domain": "emol.com",
  "title": "Título de la noticia",
  "subtitle": "Subtítulo o bajada",
  "content": "Contenido completo del artículo...",
  "author": "Nombre del Autor",
  "publish_date": "2024-01-15T10:30:00",
  "category": "Nacional",
  "timestamp": "2024-01-15T12:45:30.123Z",
  "crawler_id": "news-monitor-1",
  "content_length": 2500,
  "language": "es"
}
```

## 🛠️ Desarrollo

### Estructura del Proyecto

```
crawlers/
├── news_monitor.py      # ⭐ Archivo principal
├── run_monitor.py       # Script de ejecución
├── base/               # Utilidades básicas
├── requirements.txt    # Dependencias mínimas
├── .env               # Configuración
└── README.md          # Esta documentación
```

### Personalización

El código está diseñado para ser **fácil de modificar**:

- **Agregar sitios**: Edita `_load_site_configs()`
- **Cambiar selectores**: Modifica los selectores CSS
- **Ajustar timing**: Cambia los `await asyncio.sleep()`
- **Modificar output**: Edita `send_to_kafka()`

### Testing

```bash
# Test rápido sin Kafka
python -c "
from crawlers.news_monitor import NewsMonitor
import asyncio

async def test():
    monitor = NewsMonitor(enable_kafka=False)
    await monitor.monitor_site('emol', monitor.sites['emol'])

asyncio.run(test())
"
```

## 🤔 ¿Por qué esta Filosofía?

**Antes**: Sistema complejo con microservicios, Docker, bases de datos, schedulers, registries...

**Ahora**: Un archivo Python que hace exactamente lo que necesitamos.

**Ventajas**:
- ✅ **Fácil de entender**: Todo en un lugar
- ✅ **Fácil de modificar**: Sin abstracciones complejas
- ✅ **Fácil de debuggear**: Logs claros y directos
- ✅ **Fácil de deployar**: Solo Python + dependencias
- ✅ **Eficaz**: Hace el trabajo sin overhead

## 📈 Rendimiento

- **Memoria**: ~50MB en ejecución
- **CPU**: Mínimo (principalmente I/O)
- **Red**: ~1-2 requests/segundo por sitio
- **Throughput**: 100+ artículos/hora

## 🚨 Troubleshooting

### Problema: No encuentra artículos
**Solución**: Verifica los selectores CSS del sitio

### Problema: Error de conexión
**Solución**: Verifica tu conexión a internet y que el sitio esté disponible

### Problema: Kafka no funciona
**Solución**: Ejecuta con `enable_kafka=False` o verifica tu configuración de Kafka

## 📝 Changelog

Ver [`CHANGELOG.md`](CHANGELOG.md) para historial de cambios.

## 🤝 Contribuir

1. Fork el proyecto
2. Modifica `news_monitor.py`
3. Prueba tus cambios
4. Envía un Pull Request

**¡Mantengamos la simplicidad!** 