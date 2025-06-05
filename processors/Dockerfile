FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    DEBIAN_FRONTEND=noninteractive


# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

# Copiar el modelo localmente descargado al cache HuggingFace
RUN mkdir -p /root/.cache/huggingface/transformers
# COPY models/paraphrase-multilingual-MiniLM-L12-v2 /root/.cache/huggingface/transformers/sentence-transformers_paraphrase-multilingual-MiniLM-L12-v2