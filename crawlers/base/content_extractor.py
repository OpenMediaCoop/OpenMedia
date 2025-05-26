"""
Content extraction utilities for web crawlers.
"""

import re
import logging
from typing import Optional, List
from datetime import datetime
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from .models import Article, WebPage

logger = logging.getLogger(__name__)


class ContentExtractor:
    """Extracts structured content from HTML pages."""
    
    def __init__(self):
        if BeautifulSoup is None:
            raise ImportError("BeautifulSoup4 is required for content extraction. Install with: pip install beautifulsoup4")
    
    def extract_article(
        self,
        html: str,
        url: str,
        title_selector: Optional[str] = None,
        content_selector: Optional[str] = None,
        author_selector: Optional[str] = None,
        date_selector: Optional[str] = None,
        summary_selector: Optional[str] = None
    ) -> Optional[Article]:
        """Extract article content from HTML."""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract title
            title = self._extract_text_by_selector(soup, title_selector) or self._extract_title_fallback(soup)
            if not title:
                logger.warning(f"No title found for {url}")
                return None
            
            # Extract content
            content = self._extract_text_by_selector(soup, content_selector) or self._extract_content_fallback(soup)
            if not content:
                logger.warning(f"No content found for {url}")
                return None
            
            # Extract optional fields
            author = self._extract_text_by_selector(soup, author_selector)
            summary = self._extract_text_by_selector(soup, summary_selector)
            
            # Extract and parse date
            published_date = None
            if date_selector:
                date_text = self._extract_text_by_selector(soup, date_selector)
                if date_text:
                    published_date = self._parse_date(date_text)
            
            # Extract category from meta tags or breadcrumbs
            category = self._extract_category(soup)
            
            # Extract tags/keywords
            tags = self._extract_tags(soup)
            
            return Article(
                title=title.strip(),
                content=content.strip(),
                url=url,
                author=author.strip() if author else None,
                published_date=published_date,
                summary=summary.strip() if summary else None,
                category=category,
                tags=tags
            )
            
        except Exception as e:
            logger.error(f"Failed to extract article from {url}: {e}")
            return None
    
    def extract_webpage(
        self,
        html: str,
        url: str,
        title_selector: Optional[str] = None,
        content_selector: Optional[str] = None,
        meta_selector: Optional[str] = None
    ) -> Optional[WebPage]:
        """Extract general webpage content from HTML."""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract title
            title = self._extract_text_by_selector(soup, title_selector) or self._extract_title_fallback(soup)
            if not title:
                logger.warning(f"No title found for {url}")
                return None
            
            # Extract content
            content = self._extract_text_by_selector(soup, content_selector) or self._extract_content_fallback(soup)
            if not content:
                logger.warning(f"No content found for {url}")
                return None
            
            # Extract meta description
            description = self._extract_meta_description(soup)
            
            # Extract keywords
            keywords = self._extract_keywords(soup)
            
            # Extract language
            language = self._extract_language(soup)
            
            return WebPage(
                title=title.strip(),
                content=content.strip(),
                url=url,
                description=description,
                keywords=keywords,
                language=language
            )
            
        except Exception as e:
            logger.error(f"Failed to extract webpage from {url}: {e}")
            return None
    
    def _extract_text_by_selector(self, soup: BeautifulSoup, selector: Optional[str]) -> Optional[str]:
        """Extract text using CSS selector."""
        if not selector:
            return None
        
        try:
            # Handle special selector syntax for attributes
            if '::attr(' in selector:
                element_selector, attr = selector.split('::attr(')
                attr = attr.rstrip(')')
                element = soup.select_one(element_selector)
                return element.get(attr) if element else None
            elif '::text' in selector:
                element_selector = selector.replace('::text', '')
                element = soup.select_one(element_selector)
                return element.get_text(strip=True) if element else None
            else:
                element = soup.select_one(selector)
                return element.get_text(strip=True) if element else None
        except Exception as e:
            logger.warning(f"Failed to extract with selector '{selector}': {e}")
            return None
    
    def _extract_title_fallback(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract title using fallback methods."""
        # Try common title selectors
        selectors = [
            'h1',
            'title',
            '[property="og:title"]',
            '[name="twitter:title"]',
            '.title',
            '.headline'
        ]
        
        for selector in selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    text = element.get('content') if element.name == 'meta' else element.get_text(strip=True)
                    if text and len(text.strip()) > 0:
                        return text
            except:
                continue
        
        return None
    
    def _extract_content_fallback(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract content using fallback methods."""
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            element.decompose()
        
        # Try common content selectors
        selectors = [
            'article',
            '.content',
            '.article-content',
            '.post-content',
            '.entry-content',
            'main',
            '#content'
        ]
        
        for selector in selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    text = element.get_text(separator=' ', strip=True)
                    if text and len(text.strip()) > 100:  # Minimum content length
                        return text
            except:
                continue
        
        # Fallback to body content
        body = soup.find('body')
        if body:
            return body.get_text(separator=' ', strip=True)
        
        return None
    
    def _extract_category(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract category from meta tags or breadcrumbs."""
        # Try meta tags first
        meta_selectors = [
            '[property="article:section"]',
            '[name="category"]',
            '[property="og:section"]'
        ]
        
        for selector in meta_selectors:
            element = soup.select_one(selector)
            if element:
                content = element.get('content')
                if content:
                    return content.strip()
        
        # Try breadcrumbs
        breadcrumb_selectors = [
            '.breadcrumb a:last-child',
            '[data-testid="Breadcrumb"] a:last-child',
            'nav.breadcrumb a:last-child'
        ]
        
        for selector in breadcrumb_selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                if text:
                    return text
        
        return None
    
    def _extract_tags(self, soup: BeautifulSoup) -> List[str]:
        """Extract tags/keywords from meta tags."""
        tags = []
        
        # Try meta keywords
        keywords_meta = soup.select_one('[name="keywords"]')
        if keywords_meta:
            keywords = keywords_meta.get('content', '')
            tags.extend([tag.strip() for tag in keywords.split(',') if tag.strip()])
        
        # Try article tags
        tag_elements = soup.select('.tags a, .tag a, [rel="tag"]')
        for element in tag_elements:
            tag = element.get_text(strip=True)
            if tag and tag not in tags:
                tags.append(tag)
        
        return tags[:10]  # Limit to 10 tags
    
    def _extract_meta_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract meta description."""
        selectors = [
            '[name="description"]',
            '[property="og:description"]',
            '[name="twitter:description"]'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                content = element.get('content')
                if content:
                    return content.strip()
        
        return None
    
    def _extract_keywords(self, soup: BeautifulSoup) -> List[str]:
        """Extract keywords from meta tags."""
        keywords = []
        
        keywords_meta = soup.select_one('[name="keywords"]')
        if keywords_meta:
            content = keywords_meta.get('content', '')
            keywords = [kw.strip() for kw in content.split(',') if kw.strip()]
        
        return keywords[:10]  # Limit to 10 keywords
    
    def _extract_language(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract language from HTML attributes."""
        # Try html lang attribute
        html_element = soup.find('html')
        if html_element:
            lang = html_element.get('lang')
            if lang:
                return lang
        
        # Try meta tags
        lang_meta = soup.select_one('[http-equiv="content-language"], [name="language"]')
        if lang_meta:
            content = lang_meta.get('content')
            if content:
                return content
        
        return None
    
    def _parse_date(self, date_text: str) -> Optional[datetime]:
        """Parse date string to datetime object."""
        if not date_text:
            return None
        
        # Common date formats
        formats = [
            '%Y-%m-%dT%H:%M:%S%z',  # ISO format with timezone
            '%Y-%m-%dT%H:%M:%S',    # ISO format without timezone
            '%Y-%m-%d %H:%M:%S',    # Standard format
            '%Y-%m-%d',             # Date only
            '%d/%m/%Y',             # DD/MM/YYYY
            '%m/%d/%Y',             # MM/DD/YYYY
        ]
        
        # Clean the date text
        date_text = re.sub(r'[^\d\-/:\sT]', '', date_text.strip())
        
        for fmt in formats:
            try:
                return datetime.strptime(date_text, fmt)
            except ValueError:
                continue
        
        logger.warning(f"Could not parse date: {date_text}")
        return None 