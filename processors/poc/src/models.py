from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

Base = declarative_base()

# SQLAlchemy Models
class News(Base):
    __tablename__ = "news"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text)
    embedding = Column(Vector(1536))  # Vector dimension should match your embedding model
    summary_embedding = Column(Vector(1536))  # Vector dimension should match your embedding model
    topic_classification = Column(JSON)  # Dict[str, str]
    writing_analysis = Column(JSON)  # Dict[str, float]
    published_at = Column(DateTime)
    author_id = Column(Integer)
    facts = Column(JSON)
    entities = Column(JSON)
    keywords = Column(JSON)  # List[str]
    ambiguity_score = Column(Float)
    context_score = Column(Float)
    relevance_score = Column(Float)

    # Relationship with ScrapingMetadata
    scraping_metadata = relationship("ScrapingMetadata", back_populates="news", uselist=False)

class ScrapingMetadata(Base):
    __tablename__ = "scraping_metadata"

    id = Column(Integer, primary_key=True)
    news_id = Column(Integer, ForeignKey("news.id"), nullable=False)
    source = Column(String, nullable=False)
    url = Column(String, nullable=False)  # Stored as string, validated as HttpUrl in Pydantic
    original_published_at = Column(DateTime)
    http_status = Column(Integer)
    headers = Column(JSON)
    raw_html = Column(Text)

    # Relationship with News
    news = relationship("News", back_populates="scraping_metadata")

# Pydantic Models for Input Validation
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