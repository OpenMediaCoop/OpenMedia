from .embeddings import generate_embedding
from common.models import NewsInput
from common.storage import PgVectorStorage
from base.processor_interface import ProcessorInterface

class VectorProcessor(ProcessorInterface):
    async def process(self, payload: dict):
        embedding = generate_embedding(payload["content"])

        news = NewsInput(
            title=payload["title"],
            content=payload["content"],
            embedding=embedding
        )

        storage = PgVectorStorage()
        await storage.connect()
        return await storage.insert_news(news)