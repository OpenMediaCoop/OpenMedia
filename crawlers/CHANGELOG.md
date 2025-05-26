# Changelog - OpenMedia Crawlers

Todos los cambios notables en este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### 🚀 Agregado
- Sistema completo de crawlers distribuidos para medios chilenos
- Soporte inicial para 4 sitios de noticias chilenos:
  - El Mercurio (emol.com)
  - La Tercera (latercera.com)
  - BioBio Chile (biobiochile.cl)
  - Radio Cooperativa (cooperativa.cl)
- Arquitectura de microservicios con Docker
- Sistema de monitoreo y métricas
- Scripts de automatización y gestión
- Documentación completa (README, ARCHITECTURE)
- Makefile para operaciones comunes
- Script de validación de configuración

### 🔧 Configuración
- Docker Compose para orquestación de servicios
- Configuración modular de sitios en JSON
- Variables de entorno para desarrollo/producción
- Integración con infraestructura global (Kafka, PostgreSQL, Redis)

### 📚 Documentación
- README.md con guía de inicio rápido
- ARCHITECTURE.md con detalles técnicos
- Documentación inline en código Python
- Scripts con mensajes de ayuda

## [1.0.0] - Por liberar

### Características Principales
- **Crawler Registry**: Gestión centralizada de crawlers
- **Site Manager**: Configuración dinámica de sitios
- **URL Scheduler**: Cola inteligente de URLs
- **News Crawler**: Extracción especializada de noticias
- **Content Extractor**: Extracción robusta de contenido
- **Monitoring Service**: Observabilidad del sistema

### Tecnologías
- Python 3.11+ con Scrapy
- Docker & Docker Compose
- Redis para colas y caché
- Kafka para streaming
- PostgreSQL para persistencia
- FastAPI para servicios REST

### Scripts de Utilidad
- `setup.sh`: Configuración inicial
- `dev.sh`: Herramienta de desarrollo
- `monitor.sh`: Monitoreo del sistema
- `test.sh`: Suite de pruebas
- `validate.sh`: Validación de configuración
- `register-sites.sh`: Registro de sitios
- `start-crawling.sh`: Inicio de crawling

### Próximos Pasos
- [ ] Dashboard web de monitoreo
- [ ] Soporte para más sitios chilenos
- [ ] Análisis de sentimiento integrado
- [ ] API pública para consultas
- [ ] Detección automática de cambios en sitios 