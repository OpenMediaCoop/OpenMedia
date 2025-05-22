from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI, MONGO_DB, MONGO_COLLECTION
from models import HtmlDocument

class MongoStorage:
    def __init__(self):
        self.client = AsyncIOMotorClient(MONGO_URI)
        self.db = self.client[MONGO_DB]
        self.collection = self.db[MONGO_COLLECTION]

    async def insert_document(self, doc: HtmlDocument):
        await self.collection.insert_one(doc.dict())