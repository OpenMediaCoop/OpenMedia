# Integración con Kafka - OpenMedia Crawlers

## Información para el Equipo de Procesadores

Este documento describe los datos que el sistema de crawlers envía a Kafka para su procesamiento posterior.

## Topics de Kafka

### 1. `news_content` - Contenido de Noticias Extraído

**Descripción**: Contiene artículos de noticias completamente extraídos y estructurados.

**Formato del Mensaje**:

```json
{
  "url": "https://www.emol.com/noticias/Nacional/2024/01/15/12345/titulo-noticia.html",
  "site_id": "emol-com-uuid-12345",
  "site_name": "El Mercurio Online",
  "domain": "emol.com",
  "title": "Título completo de la noticia extraída",
  "content": "Contenido completo del artículo. Puede ser varios párrafos de texto...",
  "author": "Juan Pérez" | null,
  "publish_date": "2024-01-15T10:30:00" | null,
  "category": "Nacional" | null,
  "timestamp": "2024-01-15T12:45:30.123456Z",
  "crawler_id": "news-crawler-1",
  "status_code": 200,
  "content_length": 2500,
  "language": "es"
}
```

**Campos**:

| Campo | Tipo | Descripción | Nullable |
|-------|------|-------------|----------|
| `url` | string | URL original del artículo | No |
| `site_id` | string | ID único del sitio en el sistema | No |
| `site_name` | string | Nombre legible del sitio | No |
| `domain` | string | Dominio del sitio (ej: emol.com) | No |
| `title` | string | Título del artículo | No |
| `content` | string | Contenido completo del artículo | No |
| `author` | string | Autor del artículo | Sí |
| `publish_date` | string | Fecha de publicación (ISO 8601) | Sí |
| `category` | string | Categoría del artículo | Sí |
| `timestamp` | string | Momento de extracción (ISO 8601) | No |
| `crawler_id` | string | ID del crawler que extrajo | No |
| `status_code` | integer | Código HTTP de respuesta | No |
| `content_length` | integer | Longitud del contenido en caracteres | No |
| `language` | string | Código de idioma (ISO 639-1) | No |

### 2. `urls.discovered` - URLs Descubiertas (Futuro)

**Descripción**: URLs nuevas encontradas durante el crawling.

```json
{
  "url": "https://www.latercera.com/noticia/nueva/",
  "discovered_from": "https://www.latercera.com/",
  "site_id": "latercera-com-uuid",
  "timestamp": "2024-01-15T12:45:30.123456Z",
  "crawler_id": "news-crawler-1"
}
```

### 3. `crawl.metrics` - Métricas de Crawling (Futuro)

**Descripción**: Métricas y estadísticas del proceso de crawling.

```json
{
  "crawler_id": "news-crawler-1",
  "site_id": "biobiochile-cl-uuid",
  "url": "https://www.biobiochile.cl/",
  "success": true,
  "processing_time_ms": 1250,
  "bytes_downloaded": 125000,
  "urls_extracted": 45,
  "timestamp": "2024-01-15T12:45:30.123456Z"
}
```

## Configuración de Kafka

### Producción

- **Bootstrap Servers**: `kafka:9092` (dentro de Docker)
- **Compression**: `gzip`
- **Serialización**: JSON
- **Key**: `site_id` (para particionado por sitio)

### Consumo Recomendado

```python
# Ejemplo de consumidor Python
from kafka import KafkaConsumer
import json

consumer = KafkaConsumer(
    'news_content',
    bootstrap_servers=['kafka:9092'],
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    group_id='content-processor-group',
    auto_offset_reset='earliest'
)

for message in consumer:
    content = message.value
    print(f"Procesando artículo: {content['title']}")
    # Procesar contenido...
```

## Garantías de Entrega

- **At-least-once**: Los mensajes pueden duplicarse en caso de reintentos
- **Ordenamiento**: Por partición (site_id)
- **Retención**: Configurada en Kafka (default: 7 días)

## Validaciones del Crawler

Antes de enviar a Kafka, el crawler valida:

1. **Contenido mínimo**: Al menos 100 caracteres
2. **Título válido**: Al menos 10 caracteres
3. **No es página de error**: No contiene indicadores de 404, etc.
4. **No es página de navegación**: No es index, about, contact, etc.

## Sitios Actualmente Soportados

| Sitio | Domain | Idioma | Frecuencia Esperada |
|-------|--------|--------|---------------------|
| El Mercurio | emol.com | es | ~100-200 artículos/día |
| La Tercera | latercera.com | es | ~100-200 artículos/día |
| BioBio Chile | biobiochile.cl | es | ~150-250 artículos/día |
| Cooperativa | cooperativa.cl | es | ~100-150 artículos/día |

## Monitoreo

Para verificar que los mensajes están llegando:

```bash
# Ver últimos mensajes en el topic
docker exec -it kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic news_content \
  --from-beginning \
  --max-messages 5
```

## Contacto

Para problemas o preguntas sobre los datos:
- Revisar logs del crawler: `docker-compose logs news-crawler-1`
- Verificar métricas: `curl http://localhost:8083/metrics`

## Próximas Mejoras

1. [ ] Agregar campo `tags` con etiquetas extraídas
2. [ ] Incluir `image_url` para imagen principal
3. [ ] Extraer `related_articles` si están disponibles
4. [ ] Agregar `sentiment_hint` basado en palabras clave 