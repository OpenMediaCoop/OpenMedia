from .hashtag import generar_hashtags
from common.models import NewsInput
from common.storage import PgVectorStorage
from base.processor_interface import ProcessorInterface
import logging

logger = logging.getLogger(__name__)

class HashtagProcessor(ProcessorInterface):
    async def process(self, payload: dict):
        text = payload.get("text", "[Contenido no disponible]")
        hashtags = generar_hashtags(text)
        logger.info(f"🔖 Hashtags generados: {hashtags}")

        news = NewsInput(
            title=payload.get("title", "[Título no disponible]"),
            content=text,
            keywords=hashtags
        )

        storage = PgVectorStorage()
        await storage.connect()
        logger.info("🗃 Insertando noticia en base de datos...")
        return await storage.insert_news(news)