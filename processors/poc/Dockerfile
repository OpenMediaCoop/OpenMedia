# Dockerfile para el consumer de Scrapper Vector

FROM python:3.11-slim

# Evitar prompts de Debian
ENV DEBIAN_FRONTEND=noninteractive

# Crear el directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar las dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente dentro del contenedor
COPY src/ app/src/

# Establecer el entrypoint correcto con el módulo src.main
ENTRYPOINT ["python", "-u", "main.py"]