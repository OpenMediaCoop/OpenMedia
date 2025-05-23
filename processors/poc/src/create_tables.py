from models import Base
from config import PGVECTOR_DSN
from sqlalchemy.ext.asyncio import create_async_engine

import asyncio

async def create_all():
    engine = create_async_engine(PGVECTOR_DSN)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_all()) 