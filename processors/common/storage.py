import asyncpg
from config import PGVECTOR_DSN
from models import NewsInput, ScrapingMetadataInput
from datetime import datetime

class PgVectorStorage:
    def __init__(self):
        self.pool = None

    async def connect(self):
        if not self.pool:
            self.pool = await asyncpg.create_pool(PGVECTOR_DSN)

    async def insert_news(self, news: NewsInput) -> int:
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow("""
                INSERT INTO news (title, content, summary, embedding, summary_embedding,
                                  topic_classification, writing_analysis, published_at, author_id,
                                  facts, entities, keywords, ambiguity_score, context_score,
                                  relevance_score)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
                RETURNING id;
            """, news.title, news.content, news.summary, news.embedding, news.summary_embedding,
                 news.topic_classification, news.writing_analysis, news.published_at, news.author_id,
                 news.facts, news.entities, news.keywords, news.ambiguity_score,
                 news.context_score, news.relevance_score)
            return result["id"]

    async def insert_scraping_metadata(self, meta: ScrapingMetadataInput):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO scraping_metadata (news_id, source, url, original_published_at,
                                               http_status, headers, raw_html)
                VALUES ($1, $2, $3, $4, $5, $6, $7);
            """, meta.news_id, meta.source, meta.url, meta.original_published_at,
                 meta.http_status, meta.headers, meta.raw_html)