import asyncpg
from config import PGVECTOR_DSN
from models import NewsInput, ScrapingMetadataInput, News, ScrapingMetadata, Base
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select

class PgVectorStorage:
    def __init__(self):
        self.engine = None
        self.async_session = None

    async def connect(self):
        if not self.engine:
            # Create async engine
            self.engine = create_async_engine(PGVECTOR_DSN)
            # Create async session factory
            self.async_session = sessionmaker(
                self.engine, class_=AsyncSession, expire_on_commit=False
            )
            # Create tables
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

    async def close(self):
        if self.pool:
            await self.pool.close()

    async def insert_news(self, news: NewsInput) -> int:
        async with self.async_session() as session:
            # Create News instance from NewsInput
            news_db = News(
                title=news.title,
                content=news.content,
                summary=news.summary,
                embedding=news.embedding,
                summary_embedding=news.summary_embedding,
                topic_classification=news.topic_classification,
                writing_analysis=news.writing_analysis,
                published_at=news.published_at,
                author_id=news.author_id,
                facts=news.facts,
                entities=news.entities,
                keywords=news.keywords,
                ambiguity_score=news.ambiguity_score,
                context_score=news.context_score,
                relevance_score=news.relevance_score
            )
            
            # Add and commit
            session.add(news_db)
            await session.commit()
            await session.refresh(news_db)
            
            return news_db.id

    async def insert_scraping_metadata(self, meta: ScrapingMetadataInput):
        async with self.async_session() as session:
            # Create ScrapingMetadata instance from ScrapingMetadataInput
            meta_db = ScrapingMetadata(
                news_id=meta.news_id,
                source=meta.source,
                url=str(meta.url),  # Convert HttpUrl to string
                original_published_at=meta.original_published_at,
                http_status=meta.http_status,
                headers=meta.headers,
                raw_html=meta.raw_html
            )
            
            # Add and commit
            session.add(meta_db)
            await session.commit()