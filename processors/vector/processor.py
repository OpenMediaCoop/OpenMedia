from .embeddings import generate_embedding
from common.models import NewsInput
from common.storage import PgVectorStorage
from base.processor_interface import ProcessorInterface

class VectorProcessor(ProcessorInterface):
    async def process(self, payload: dict):
        embedding = generate_embedding(payload.get("text", "[Contenido no disponible]"))

        news = NewsInput(
            title=payload.get("title", "[Título no disponible]"),
            content=payload.get("text", "[Contenido no disponible]"),
            embedding=embedding
        )

        storage = PgVectorStorage()
        await storage.connect()
        return await storage.insert_news(news)