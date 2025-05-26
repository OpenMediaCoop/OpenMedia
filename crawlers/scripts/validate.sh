#!/bin/bash

# Script de validación para el sistema de crawlers

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔍 Validando configuración del sistema de crawlers...${NC}"
echo "=================================================="

ERRORS=0
WARNINGS=0

# Función para reportar errores
error() {
    echo -e "${RED}❌ ERROR: $1${NC}"
    ERRORS=$((ERRORS + 1))
}

# Función para reportar warnings
warning() {
    echo -e "${YELLOW}⚠️  WARNING: $1${NC}"
    WARNINGS=$((WARNINGS + 1))
}

# Función para reportar éxito
success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# 1. Verificar Docker
echo -e "\n${BLUE}1. Verificando Docker...${NC}"
if command -v docker &> /dev/null; then
    success "Docker instalado: $(docker --version)"
else
    error "Docker no está instalado"
fi

if command -v docker-compose &> /dev/null; then
    success "Docker Compose instalado: $(docker-compose --version)"
else
    error "Docker Compose no está instalado"
fi

# 2. Verificar archivos de configuración
echo -e "\n${BLUE}2. Verificando archivos de configuración...${NC}"

# Verificar docker-compose.yaml
if [ -f "docker-compose.yaml" ]; then
    if docker-compose config -q 2>/dev/null; then
        success "docker-compose.yaml es válido"
    else
        error "docker-compose.yaml tiene errores de sintaxis"
    fi
else
    error "docker-compose.yaml no encontrado"
fi

# Verificar configuración de sitios
if [ -f "config/sites/chile_news.json" ]; then
    if python -m json.tool config/sites/chile_news.json > /dev/null 2>&1; then
        success "chile_news.json es válido"
        
        # Contar sitios configurados
        site_count=$(python -c "import json; data=json.load(open('config/sites/chile_news.json')); print(len(data['sites']))" 2>/dev/null || echo "0")
        success "Sitios configurados: $site_count"
    else
        error "chile_news.json tiene errores de sintaxis JSON"
    fi
else
    error "config/sites/chile_news.json no encontrado"
fi

# 3. Verificar permisos de scripts
echo -e "\n${BLUE}3. Verificando permisos de scripts...${NC}"
for script in scripts/*.sh; do
    if [ -x "$script" ]; then
        success "$(basename $script) es ejecutable"
    else
        warning "$(basename $script) no es ejecutable"
        chmod +x "$script"
        success "$(basename $script) ahora es ejecutable"
    fi
done

# 4. Verificar puertos disponibles
echo -e "\n${BLUE}4. Verificando puertos disponibles...${NC}"
PORTS=(6380 8080 8081 8082 8083)
for port in "${PORTS[@]}"; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        error "Puerto $port ya está en uso"
    else
        success "Puerto $port disponible"
    fi
done

# 5. Verificar red Docker
echo -e "\n${BLUE}5. Verificando red Docker...${NC}"
if docker network ls | grep -q "scrapper-net"; then
    success "Red scrapper-net existe"
else
    warning "Red scrapper-net no existe, se creará al iniciar"
fi

# 6. Verificar espacio en disco
echo -e "\n${BLUE}6. Verificando espacio en disco...${NC}"
available_space=$(df -h . | awk 'NR==2 {print $4}')
success "Espacio disponible: $available_space"

# 7. Verificar variables de entorno
echo -e "\n${BLUE}7. Verificando variables de entorno...${NC}"
if [ -f ".env" ]; then
    success "Archivo .env encontrado"
else
    if [ -f "env.example" ]; then
        warning "Archivo .env no encontrado, copiando desde env.example"
        cp env.example .env
        success "Archivo .env creado"
    else
        error "No se encontró .env ni env.example"
    fi
fi

# 8. Verificar directorios necesarios
echo -e "\n${BLUE}8. Verificando directorios...${NC}"
REQUIRED_DIRS=("logs" "data" "config/sites")
for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        success "Directorio $dir existe"
    else
        warning "Directorio $dir no existe, creando..."
        mkdir -p "$dir"
        success "Directorio $dir creado"
    fi
done

# 9. Verificar infraestructura global
echo -e "\n${BLUE}9. Verificando infraestructura global...${NC}"
if [ -f "../docker-compose.global.yaml" ]; then
    success "docker-compose.global.yaml encontrado"
    
    # Verificar si los servicios globales están corriendo
    GLOBAL_SERVICES=("kafka" "zookeeper" "pgvector")
    for service in "${GLOBAL_SERVICES[@]}"; do
        if docker ps | grep -q "$service"; then
            success "$service está corriendo"
        else
            warning "$service no está corriendo"
        fi
    done
else
    error "../docker-compose.global.yaml no encontrado"
fi

# 10. Verificar Python (opcional para desarrollo)
echo -e "\n${BLUE}10. Verificando Python (opcional)...${NC}"
if command -v python3 &> /dev/null; then
    python_version=$(python3 --version)
    success "Python instalado: $python_version"
    
    # Verificar venv
    if [ -d "venv" ]; then
        success "Virtual environment existe"
    else
        warning "Virtual environment no existe (usa 'make dev-local' para crear)"
    fi
else
    warning "Python no instalado (solo necesario para desarrollo local)"
fi

# Resumen
echo -e "\n${BLUE}=================================================="
echo -e "📊 Resumen de Validación${NC}"
echo -e "=================================================="

if [ $ERRORS -eq 0 ]; then
    if [ $WARNINGS -eq 0 ]; then
        echo -e "${GREEN}✅ Sistema listo para iniciar!${NC}"
        echo -e "\nEjecuta: ${BLUE}make start${NC} o ${BLUE}./scripts/dev.sh start${NC}"
    else
        echo -e "${YELLOW}⚠️  Sistema puede iniciar con $WARNINGS advertencias${NC}"
        echo -e "\nRevisa las advertencias arriba antes de continuar"
    fi
else
    echo -e "${RED}❌ Se encontraron $ERRORS errores que deben ser corregidos${NC}"
    echo -e "\nCorrige los errores antes de iniciar el sistema"
    exit 1
fi

echo "" 