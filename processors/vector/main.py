import asyncio
import logging  # 👈 agregar esto
from .consumer import consume

# Config global de logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
)

# Silenciar ruido de librerías externas
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
logging.getLogger("transformers").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)
logging.getLogger("aiokafka").setLevel(logging.INFO)

if __name__ == "__main__":
    asyncio.run(consume())