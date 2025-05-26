from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict
from datetime import datetime

class NewsInput(BaseModel):
    title: str
    content: str
    summary: Optional[str] = None
    embedding: Optional[List[float]] = None
    summary_embedding: Optional[List[float]] = None
    topic_classification: Optional[Dict[str, str]] = None
    writing_analysis: Optional[Dict[str, float]] = None
    published_at: Optional[datetime] = None
    author_id: Optional[int] = None
    facts: Optional[Dict] = None
    entities: Optional[Dict] = None
    keywords: Optional[List[str]] = None
    ambiguity_score: Optional[float] = None
    context_score: Optional[float] = None
    relevance_score: Optional[float] = None

class ScrapingMetadataInput(BaseModel):
    news_id: int
    source: str
    url: HttpUrl
    original_published_at: Optional[datetime] = None
    http_status: Optional[int] = None
    headers: Optional[Dict] = None
    raw_html: Optional[str] = None