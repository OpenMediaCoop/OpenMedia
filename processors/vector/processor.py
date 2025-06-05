from .embeddings import generate_embedding
from common.models import NewsInput
from common.storage import PgVectorStorage
from base.processor_interface import ProcessorInterface
import logging

logger = logging.getLogger(__name__)

class VectorProcessor(ProcessorInterface):
    async def process(self, payload: dict):
        embedding = generate_embedding(text=payload.get("text", "[Contenido no disponible]"), model_name="paraphrase-multilingual-MiniLM-L12-v2")
        logger.info(f"🧠 Embedding generado con {len(embedding)} dimensiones")

        news = NewsInput(
            title=payload.get("title", "[Título no disponible]"),
            content=payload.get("text", "[Contenido no disponible]"),
            embedding=embedding
        )

        storage = PgVectorStorage()
        await storage.connect()
        logger.info("🗃 Insertando noticia en base de datos...")
        return await storage.insert_news(news)