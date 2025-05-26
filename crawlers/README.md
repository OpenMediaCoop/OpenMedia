# OpenMedia Crawlers System

Sistema distribuido de crawlers especializados en medios de comunicación chilenos.

## 🚀 Quick Start

```bash
# 1. Configurar el entorno
./scripts/setup.sh

# 2. Iniciar todo automáticamente
./scripts/dev.sh start

# 3. Monitorear el sistema
./scripts/monitor.sh watch
```

## 📋 Requisitos

- Docker & Docker Compose
- Python 3.11+ (para desarrollo local)
- 4GB RAM mínimo
- 10GB espacio en disco

## 🏗️ Arquitectura

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│ News Crawler 1  │────▶│    Kafka     │────▶│ Processors  │
└─────────────────┘     └──────────────┘     └─────────────┘
        │                                              │
        ▼                                              ▼
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│  URL Scheduler  │────▶│    Redis     │     │  PostgreSQL │
└─────────────────┘     └──────────────┘     └─────────────┘
        │
        ▼
┌─────────────────┐     ┌──────────────┐
│ Site Manager    │────▶│   Registry   │
└─────────────────┘     └──────────────┘
```

## 📦 Componentes

### Crawlers
- **NewsCrawler**: Especializado en extracción de noticias
- **BaseCrawler**: Framework base extensible

### Servicios
- **Registry** (8080): Registro y monitoreo de crawlers
- **Site Manager** (8081): Gestión de configuraciones de sitios
- **URL Scheduler** (8082): Cola de URLs y priorización
- **Monitoring** (8083): Métricas y observabilidad

### Infraestructura
- **Kafka**: Streaming de contenido extraído
- **Redis**: Cola de URLs y caché
- **PostgreSQL**: Almacenamiento persistente

## 🌐 Sitios Chilenos Soportados

| Sitio | Estado | Prioridad | Rate Limit |
|-------|--------|-----------|------------|
| El Mercurio (emol.com) | ✅ Activo | Alta | 30 req/min |
| La Tercera | ✅ Activo | Alta | 40 req/min |
| BioBio Chile | ✅ Activo | Media | 50 req/min |
| Cooperativa | ✅ Activo | Media | 35 req/min |

## 🛠️ Desarrollo

### Configuración Local

```bash
# Copiar variables de entorno
cp env.example .env

# Instalar dependencias Python (opcional)
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### Comandos Útiles

```bash
# Gestión de servicios
./scripts/dev.sh start      # Iniciar todo
./scripts/dev.sh stop       # Detener todo
./scripts/dev.sh restart    # Reiniciar
./scripts/dev.sh logs <servicio>  # Ver logs

# Monitoreo
./scripts/monitor.sh        # Estado del sistema
./scripts/monitor.sh watch  # Monitoreo continuo
./scripts/monitor.sh stats  # Estadísticas detalladas

# Testing
./scripts/test.sh          # Ejecutar todos los tests
./scripts/test.sh health   # Solo health checks
./scripts/test.sh api      # Solo tests de API
```

### Agregar un Nuevo Sitio

1. Editar `config/sites/chile_news.json`
2. Agregar configuración del sitio:
```json
{
  "domain": "nuevositio.cl",
  "name": "Nuevo Sitio",
  "selectors": {
    "title": "h1.titulo::text",
    "content": ".contenido p::text"
  },
  "crawl_delay": 1.5,
  "rate_limit": 40
}
```
3. Reiniciar servicios: `./scripts/dev.sh restart`

## 📊 Monitoreo y Métricas

### Endpoints de Salud

- Registry: http://localhost:8080/health
- Site Manager: http://localhost:8081/health
- Scheduler: http://localhost:8082/health
- Monitoring: http://localhost:8083/metrics

### Métricas Disponibles

- Requests por minuto
- URLs en cola
- Tasa de éxito/fallo
- Latencia promedio
- Contenido extraído

## 📨 Formato de Datos para Kafka

### Topic: `news_content`

Cuando el crawler extrae contenido de una noticia, envía el siguiente objeto JSON a Kafka:

```json
{
  "url": "https://www.emol.com/noticias/...",
  "site_id": "emol-com-12345",
  "site_name": "El Mercurio Online",
  "domain": "emol.com",
  "title": "Título de la noticia",
  "content": "Contenido completo del artículo...",
  "author": "Nombre del Autor",
  "publish_date": "2024-01-15T10:30:00",
  "category": "Nacional",
  "timestamp": "2024-01-15T12:45:30.123Z",
  "crawler_id": "news-crawler-1",
  "status_code": 200,
  "content_length": 2500,
  "language": "es"
}
```

**Campos principales:**
- `url`: URL original del artículo
- `site_id`: ID único del sitio
- `title`: Título extraído
- `content`: Contenido completo del artículo
- `author`: Autor (puede ser null)
- `publish_date`: Fecha de publicación (puede ser null)
- `timestamp`: Momento de extracción

## 🐛 Troubleshooting

### Problemas Comunes

**1. Servicios no inician**
```bash
# Verificar logs
docker-compose logs <servicio>

# Reiniciar con limpieza
./scripts/dev.sh clean
./scripts/dev.sh start
```

**2. Crawler no extrae contenido**
```bash
# Verificar selectores
./scripts/test.sh registration

# Ver logs del crawler
docker-compose logs news-crawler-1
```

**3. Redis connection refused**
```bash
# Verificar que Redis esté corriendo
docker ps | grep redis

# Reiniciar Redis
docker-compose restart redis
```

## 📝 Estructura del Proyecto

```
crawlers/
├── base/                  # Módulos base
│   ├── interfaces.py     # Contratos
│   ├── models.py         # Modelos de datos
│   ├── utils.py          # Utilidades
│   └── content_extractor.py
├── crawlers/             # Implementaciones
│   ├── base_crawler.py   # Crawler base
│   └── news_crawler.py   # Crawler de noticias
├── services/             # Microservicios
│   ├── registry/         # Registro de crawlers
│   ├── site_manager/     # Gestión de sitios
│   ├── scheduler/        # Programador de URLs
│   └── monitoring/       # Monitoreo
├── config/              # Configuraciones
│   └── sites/           # Configuraciones de sitios
├── scripts/             # Scripts de utilidad
└── docker-compose.yaml  # Orquestación
```

## 🤝 Contribuir

1. Fork el proyecto
2. Crear feature branch (`git checkout -b feature/NuevoSitio`)
3. Commit cambios (`git commit -am 'Agregar soporte para NuevoSitio'`)
4. Push al branch (`git push origin feature/NuevoSitio`)
5. Crear Pull Request

## 📄 Licencia

Este proyecto es parte de OpenMedia y está bajo la licencia especificada en el archivo LICENSE del repositorio principal. 