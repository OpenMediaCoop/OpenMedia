"""
Data models for crawler content extraction.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime

# Re-export from interfaces
from .interfaces import CrawlResult


@dataclass
class Article:
    """Represents an extracted news article."""
    title: str
    content: str
    url: str
    author: Optional[str] = None
    published_date: Optional[datetime] = None
    summary: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    extracted_at: datetime = field(default_factory=datetime.utcnow)
    
    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'title': self.title,
            'content': self.content,
            'url': self.url,
            'author': self.author,
            'published_date': self.published_date.isoformat() if self.published_date else None,
            'summary': self.summary,
            'category': self.category,
            'tags': self.tags,
            'metadata': self.metadata,
            'extracted_at': self.extracted_at.isoformat()
        }


@dataclass
class WebPage:
    """Represents an extracted web page."""
    title: str
    content: str
    url: str
    description: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    language: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    extracted_at: datetime = field(default_factory=datetime.utcnow)
    
    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'title': self.title,
            'content': self.content,
            'url': self.url,
            'description': self.description,
            'keywords': self.keywords,
            'language': self.language,
            'metadata': self.metadata,
            'extracted_at': self.extracted_at.isoformat()
        } 