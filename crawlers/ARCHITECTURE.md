# Arquitectura del Sistema de Crawlers

## Visión General

El sistema de crawlers de OpenMedia está diseñado como una arquitectura distribuida de microservicios, optimizada para la extracción escalable de contenido de medios de comunicación chilenos.

## Principios de Diseño

1. **Modularidad**: Cada componente tiene una responsabilidad única y bien definida
2. **Escalabilidad**: Los crawlers pueden escalar horizontalmente según demanda
3. **Resiliencia**: Tolerancia a fallos con reintentos y circuit breakers
4. **Observabilidad**: Monitoreo completo de métricas y logs estructurados
5. **Respeto a los sitios**: Rate limiting y políticas de cortesía

## Componentes del Sistema

### 1. Crawler Registry (Puerto 8080)

**Responsabilidad**: Registro central y coordinación de crawlers

**Funciones principales**:
- Registro/desregistro de instancias de crawler
- Asignación de sitios a crawlers
- Heartbeat monitoring
- Balanceo de carga

**API Endpoints**:
```
POST   /crawlers              # Registrar crawler
DELETE /crawlers/{id}         # Desregistrar crawler
POST   /crawlers/{id}/heartbeat
GET    /crawlers              # Listar crawlers activos
GET    /status                # Estado del sistema
```

### 2. Site Manager (Puerto 8081)

**Responsabilidad**: Gestión de configuraciones de sitios web

**Funciones principales**:
- CRUD de configuraciones de sitios
- Validación de selectores
- Gestión de políticas de crawling
- Distribución de configuraciones

**API Endpoints**:
```
POST   /sites                 # Crear sitio
GET    /sites                 # Listar sitios
GET    /sites/{id}           # Obtener sitio
PUT    /sites/{id}           # Actualizar sitio
DELETE /sites/{id}           # Eliminar sitio
POST   /sites/bulk           # Carga masiva
```

### 3. URL Scheduler (Puerto 8082)

**Responsabilidad**: Cola de URLs y programación de crawling

**Funciones principales**:
- Cola de prioridad para URLs
- Deduplicación de URLs
- Respeto a crawl delays
- Gestión de reintentos

**API Endpoints**:
```
POST   /urls                  # Agregar URL
POST   /urls/batch           # Agregar múltiples URLs
GET    /urls/next            # Obtener siguiente URL
POST   /urls/{id}/complete   # Marcar como completada
GET    /queue/size           # Tamaño de la cola
```

### 4. Monitoring Service (Puerto 8083)

**Responsabilidad**: Métricas y observabilidad del sistema

**Funciones principales**:
- Agregación de métricas
- Health checks
- Alertas
- Dashboards

**Métricas clave**:
- Requests por minuto/hora
- Tasa de éxito/fallo
- Latencia promedio
- URLs en cola
- Contenido extraído

### 5. News Crawler

**Responsabilidad**: Extracción especializada de noticias

**Características**:
- Extracción de artículos completos
- Detección de metadatos (autor, fecha, categoría)
- Validación de contenido
- Envío a Kafka

**Flujo de procesamiento**:
1. Obtiene URL del scheduler
2. Descarga página con Scrapy
3. Extrae contenido con selectores
4. Valida y estructura datos
5. Envía a Kafka
6. Extrae y programa nuevos links

## Flujo de Datos

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Browser   │────▶│Site Manager │────▶│  Registry   │
└─────────────┘     └─────────────┘     └─────────────┘
                            │                    │
                            ▼                    ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Crawler   │◀────│  Scheduler  │◀────│   Redis     │
└─────────────┘     └─────────────┘     └─────────────┘
        │                                        │
        ▼                                        │
┌─────────────┐     ┌─────────────┐            │
│    Kafka    │────▶│ Processors  │            │
└─────────────┘     └─────────────┘            │
        │                   │                    │
        ▼                   ▼                    │
┌─────────────┐     ┌─────────────┐            │
│ PostgreSQL  │◀────│   Vector    │◀───────────┘
└─────────────┘     └─────────────┘
```

## Almacenamiento

### Redis
- **Propósito**: Cache y cola de URLs
- **Estructura**:
  - DB 0: Registry (crawlers activos)
  - DB 1: Site Manager (configuraciones)
  - DB 2: URL Scheduler (cola de URLs)
  - DB 3: Monitoring (métricas)

### PostgreSQL
- **Propósito**: Almacenamiento persistente
- **Tablas principales**:
  - articles: Artículos extraídos
  - crawl_logs: Historial de crawling
  - site_configs: Configuraciones de sitios

### Kafka
- **Propósito**: Streaming de eventos
- **Topics**:
  - `content.extracted`: Contenido extraído
  - `urls.discovered`: URLs descubiertas
  - `crawl.metrics`: Métricas de crawling

## Estrategias de Escalamiento

### Horizontal
- **Crawlers**: Múltiples instancias por tipo
- **Redis**: Clustering para alta disponibilidad
- **Kafka**: Particiones múltiples por topic

### Vertical
- **Recursos**: Ajuste de CPU/memoria por servicio
- **Concurrencia**: Configuración de workers

## Políticas de Crawling

### Rate Limiting
- Respeto a robots.txt
- Delays configurables por sitio
- Backoff exponencial en errores

### Priorización
- Sitios de alta prioridad primero
- URLs más recientes primero
- Balanceo entre dominios

## Seguridad

### Autenticación
- API keys para servicios externos
- JWT para comunicación interna

### Red
- Comunicación en red privada Docker
- Exposición mínima de puertos

### Datos
- Sanitización de inputs
- Validación de URLs
- Prevención de loops infinitos

## Monitoreo y Alertas

### Logs
- Formato: JSON estructurado
- Nivel: Configurable por servicio
- Agregación: ELK stack (futuro)

### Métricas
- Prometheus format
- Grafana dashboards (futuro)
- Alertas por umbrales

### Health Checks
- Endpoint /health en cada servicio
- Verificación de dependencias
- Auto-recuperación

## Manejo de Errores

### Niveles de Retry
1. **Network errors**: 3 reintentos con backoff
2. **HTTP 5xx**: 2 reintentos después de 1 minuto
3. **Parse errors**: Log y continuar
4. **Rate limit**: Pause y retry después del delay

### Circuit Breaker
- Umbral: 5 fallos consecutivos
- Tiempo de espera: 5 minutos
- Half-open: 1 request de prueba

## Optimizaciones

### Performance
- Connection pooling
- Async I/O donde sea posible
- Batch processing de URLs

### Recursos
- Límites de memoria por contenedor
- CPU shares configurables
- Cleanup automático de datos antiguos

## Evolución Futura

### Corto Plazo
- [ ] Soporte para más sitios chilenos
- [ ] Dashboard web de monitoreo
- [ ] API pública para consultas

### Mediano Plazo
- [ ] Machine Learning para extracción
- [ ] Detección automática de cambios en sitios
- [ ] Análisis de sentimiento integrado

### Largo Plazo
- [ ] Soporte multi-idioma
- [ ] Crawling de redes sociales
- [ ] Análisis de multimedia (imágenes/videos) 