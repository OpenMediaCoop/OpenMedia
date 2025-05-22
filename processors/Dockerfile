FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY processors/ processors/

WORKDIR /app/processors

# Este CMD será sobrescrito por cada servicio en docker-compose
CMD ["python", "-m", "vector.consumer"]