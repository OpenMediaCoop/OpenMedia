from common.models import NewsInput
from common.storage import PgVectorStorage
from processors.base.processor_interface import ProcessorInterface

class RegisterProcessor(ProcessorInterface):
    async def process(self, payload: dict):
        news = NewsInput(
            title=payload["title"],
            content=payload["content"],
        )

        storage = PgVectorStorage()
        await storage.connect()
        return await storage.insert_news(news)