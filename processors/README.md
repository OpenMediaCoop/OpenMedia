# 🧠 Procesadores del Proyecto OpenMedia

Este módulo contiene todos los **processors** encargados de transformar, enriquecer y persistir los datos extraídos por el sistema de scraping, basándose en una arquitectura **Pub/Sub + PostgreSQL (pgvector)**.

Cada processor es un microcomponente autónomo que escucha un tópico específico de Kafka, ejecuta un tipo de procesamiento (resumen, embeddings, calidad, etc.) y guarda los resultados en las tablas normalizadas del esquema `news` y relacionadas.

---

## 📦 Estructura del módulo

```
processors/
├── base/             # Interfaces y utilidades compartidas entre processors
│   ├── processor_interface.py
│   └── utils.py
├── common/           # Modelos, config y almacenamiento compartido
│   ├── models.py
│   ├── storage.py
│   ├── config.py
│   └── embeddings.py
├── vector/           # Processor que genera y guarda embeddings semánticos
│   ├── processor.py
│   ├── handler.py
│   └── consumer.py
├── summary/          # Processor que genera resúmenes automáticos
├── quality/          # Processor que evalúa calidad periodística
└── hashtags/         # Processor que genera etiquetas automáticas
```

---

## 🚀 ¿Cómo funciona cada processor?

Cada carpeta contiene un `processor.py` que implementa la lógica, un `handler.py` que actúa como adaptador del mensaje, y un `consumer.py` que escucha desde Kafka:

```
Kafka Topic → consumer.py → handler.py → processor.py → PostgreSQL
```

Todos los processors implementan la interfaz común `ProcessorInterface` que define:

```python
async def process(self, payload: dict) -> Any:
    ...
```

---

## ✅ Reglas de diseño

- Cada processor debe ser **autónomo y desacoplado**.
- Debe almacenar en la base de datos solo lo que le corresponde (embeddings, resumen, scores, etc.).
- Puede compartir lógica vía `common/` (embeddings, modelos, storage, config).
- Puede extender la interfaz base desde `base/processor_interface.py`.

---

## 🧪 Pruebas

Cada processor puede ser testeado de forma independiente ejecutando su `handler.py` con datos de ejemplo, o simulado en tests.

---

## 📚 Documentación complementaria

- [Estructura de base de datos en SQL](../database/OpenMedia_v0.2.sql)
- [Diseño de arquitectura general](../.docs/diagrams/processors/perplexity-research.md)

---

## 🐳 Uso con Docker Compose

Este módulo está diseñado para ser ejecutado con un `Dockerfile` único, ubicado en `processors/Dockerfile`, que puede ser reutilizado por múltiples servicios Docker.

Cada processor define su punto de entrada modificando el comando de ejecución:

```yaml
command: ["python", "-m", "vector.consumer"]
```

Por ejemplo, para lanzar el `summary.processor` en Docker Compose:

```yaml
summary-processor:
  build:
    context: ./processors
    dockerfile: Dockerfile
  command: ["python", "-m", "summary.consumer"]
  environment:
    KAFKA_TOPIC: summary.topic
    ...
```

Asegúrate de que todos los módulos tengan un `__init__.py` para que puedan ser importados correctamente como paquetes de Python (`python -m`).

El contexto del build debe ser `./processors`, ya que el `Dockerfile` se encuentra ahí, y así se asegura que los módulos `common/`, `base/` y todos los `processor/` estén disponibles.

---