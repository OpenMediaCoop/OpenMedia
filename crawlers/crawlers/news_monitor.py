"""
Simplified News Monitor for Chilean news sites.
Continuously monitors news homepages and extracts article content.
"""

import asyncio
import time
import json
import re
from datetime import datetime
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from kafka import KafkaProducer
import structlog

from base.utils import setup_logging, get_config, normalize_url


class NewsMonitor:
    """
    Monitors news websites and extracts article content in real-time.
    Designed to run continuously and send all content to Kafka.
    """
    
    def __init__(self, enable_kafka=True):
        self.config = get_config()
        setup_logging(service_name="news-monitor")
        self.logger = structlog.get_logger("news-monitor")
        
        # Initialize Kafka producer only if enabled
        self.kafka_enabled = enable_kafka
        self.kafka_producer = None
        if enable_kafka:
            try:
                self.kafka_producer = self._init_kafka()
            except Exception as e:
                self.logger.warning("Failed to initialize Kafka, running without it", error=str(e))
                self.kafka_enabled = False
        
        # Site configurations
        self.sites = self._load_site_configs()
        
        # Request session for better performance
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Monitoring stats
        self.stats = {
            'articles_found': 0,
            'articles_processed': 0,
            'errors': 0,
            'start_time': datetime.utcnow()
        }
    
    def _init_kafka(self) -> KafkaProducer:
        """Initialize Kafka producer."""
        kafka_config = self.config.get('kafka', {})
        return KafkaProducer(
            bootstrap_servers=kafka_config.get('bootstrap_servers', 'kafka:9092'),
            value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None
        )
    
    def _load_site_configs(self) -> Dict[str, Dict[str, Any]]:
        """Load site configurations for Chilean news sites."""
        # For now, hardcoded configs. Later can load from site manager
        return {
            'emol': {
                'name': 'El Mercurio Online',
                'domain': 'emol.com',
                'homepage': 'https://www.emol.com/noticias/',
                'article_pattern': r'/noticias/[^/]+/\d{4}/\d{2}/\d{2}/\d+/',
                'selectors': {
                    'article_links': 'a[href*="/noticias/"]',
                    'title': 'h1#cuDetalle_cuTitular_tituloNoticia',
                    'subtitle': 'h2#cuDetalle_cuTitular_bajadaNoticia',
                    'content': 'div#cuDetalle_cuTexto_textoNoticia',
                    'author': 'div.info-notaemol-porfecha',
                    'date': 'meta[property="article:published_time"]',
                    # Metadatos del <head>
                    'meta_title': 'title',
                    'meta_description': 'meta[name="description"]',
                    'meta_keywords': 'meta[name="keywords"]',
                    'meta_author': 'meta[name="author"]',
                    'canonical_url': 'link[rel="canonical"]',
                    # Open Graph
                    'og_title': 'meta[property="og:title"]',
                    'og_description': 'meta[property="og:description"]',
                    'og_image': 'meta[property="og:image"]',
                    'og_url': 'meta[property="og:url"]',
                    'og_site_name': 'meta[property="og:site_name"]',
                    # Twitter Cards
                    'twitter_title': 'meta[name="twitter:title"]',
                    'twitter_description': 'meta[name="twitter:description"]',
                    'twitter_image': 'meta[name="twitter:image"]',
                    'twitter_card': 'meta[name="twitter:card"]',
                    # JSON-LD structured data
                    'json_ld': 'script[type="application/ld+json"]'
                }
            },
            'latercera': {
                'name': 'La Tercera',
                'domain': 'latercera.com',
                'homepage': 'https://www.latercera.com/',
                'article_pattern': r'/noticia/',
                'use_json_ld': True,  # Priorizar JSON-LD
                'selectors': {
                    'article_links': 'a[href*="/noticia/"]',
                    'title': 'h1.article-head__title',
                    'subtitle': 'h2.article-head__subtitle',
                    'content': 'main.article-right-rail__main',
                    'content_paragraphs': 'p.article-body__paragraph',
                    'author': 'span.article-body__byline__authors',
                    'author_link': 'a.article-body__byline__author',
                    'date': 'time.article-body__byline__date',
                    # Metadatos del <head>
                    'meta_title': 'title',
                    'meta_description': 'meta[name="description"]',
                    'meta_keywords': 'meta[name="keywords"]',
                    'meta_author': 'meta[name="author"]',
                    'canonical_url': 'link[rel="canonical"]',
                    # Open Graph
                    'og_title': 'meta[property="og:title"]',
                    'og_description': 'meta[property="og:description"]',
                    'og_image': 'meta[property="og:image"]',
                    'og_url': 'meta[property="og:url"]',
                    'og_site_name': 'meta[property="og:site_name"]',
                    # Twitter Cards
                    'twitter_title': 'meta[name="twitter:title"]',
                    'twitter_description': 'meta[name="twitter:description"]',
                    'twitter_image': 'meta[name="twitter:image"]',
                    'twitter_card': 'meta[name="twitter:card"]',
                    # JSON-LD structured data
                    'json_ld': 'script[type="application/ld+json"]'
                }
            },
            'biobio': {
                'name': 'BioBio Chile',
                'domain': 'biobiochile.cl',
                'homepage': 'https://www.biobiochile.cl/',
                'article_pattern': r'/noticias/',
                'use_json_ld': True,  # Priorizar JSON-LD como La Tercera
                'selectors': {
                    'article_links': 'a[href*="/noticias/"]',
                    # Selectores principales de contenido
                    'title': 'h1',
                    'subtitle': 'h2.bajada',
                    'content': '.post .post-content',  # Contenedor principal del artículo
                    'content_paragraphs': '.post .post-content p',  # Párrafos específicos
                    'author': '.autores',  # Selector específico para autores
                    'author_link': '.autores a',  # Enlaces de autor si existen
                    'date': 'time',
                    'date_published': 'meta[itemprop="datePublished"]',  # Microdatos
                    'date_modified': 'meta[itemprop="dateModified"]',
                    
                    # Elementos específicos de BioBio
                    'article_id': 'meta[name="identrada"]',  # ID interno de la nota
                    'article_section': 'meta[itemprop="articleSection"]',  # Sección del artículo
                    'destacador': '.destacador',  # Frases destacadas
                    'lee_tambien': '.lee-tambien-bbcl',  # Secciones "Leer también"
                    'wp_caption': '.wp-caption',  # Leyendas de imágenes
                    'audio_elements': '.wp-audio-shortcode',  # Elementos de audio
                    
                    # Metadatos del <head>
                    'meta_title': 'title',
                    'meta_description': 'meta[name="description"]',
                    'meta_keywords': 'meta[name="keywords"]',
                    'meta_news_keywords': 'meta[name="news_keywords"]',  # Keywords específicas de noticias
                    'meta_author': 'meta[name="author"]',
                    'canonical_url': 'link[rel="canonical"]',
                    'amp_url': 'link[rel="amphtml"]',  # URL de versión AMP
                    
                    # Open Graph (Facebook)
                    'og_title': 'meta[property="og:title"]',
                    'og_description': 'meta[property="og:description"]',
                    'og_image': 'meta[property="og:image"]',
                    'og_url': 'meta[property="og:url"]',
                    'og_site_name': 'meta[property="og:site_name"]',
                    'og_type': 'meta[property="og:type"]',
                    'og_article_author': 'meta[property="article:author"]',
                    'og_article_section': 'meta[property="article:section"]',
                    'og_article_published_time': 'meta[property="article:published_time"]',
                    'og_article_modified_time': 'meta[property="article:modified_time"]',
                    
                    # Twitter Cards
                    'twitter_title': 'meta[name="twitter:title"]',
                    'twitter_description': 'meta[name="twitter:description"]',
                    'twitter_image': 'meta[name="twitter:image"]',
                    'twitter_card': 'meta[name="twitter:card"]',
                    'twitter_site': 'meta[name="twitter:site"]',
                    'twitter_creator': 'meta[name="twitter:creator"]',
                    
                    # Facebook específicos
                    'fb_pages': 'meta[property="fb:pages"]',
                    'fb_app_id': 'meta[property="fb:app_id"]',
                    'fb_admins': 'meta[property="fb:admins"]',
                    
                    # Favicons y Apple Touch Icons
                    'favicon': 'link[rel="icon"]',
                    'apple_touch_icon': 'link[rel="apple-touch-icon"]',
                    
                    # JSON-LD structured data
                    'json_ld': 'script[type="application/ld+json"]',
                    
                    # Atributos de datos específicos
                    'data_id_nota': 'head[data-id-nota]'  # ID de nota desde atributo data
                }
            }
        }
    
    async def start(self):
        """Start monitoring all configured sites."""
        self.logger.info("Starting news monitor", sites=list(self.sites.keys()))
        
        while True:
            try:
                for site_id, site_config in self.sites.items():
                    if site_config.get('enabled', True):
                        await self.monitor_site(site_id, site_config)
                
                # Wait before next scan cycle
                await asyncio.sleep(60)  # 1 minute
                
            except Exception as e:
                self.logger.error("Error in monitor loop", error=str(e))
                await asyncio.sleep(30)
    
    async def monitor_site(self, site_id: str, site_config: Dict[str, Any]):
        """Monitor a single news site."""
        try:
            self.logger.info("Monitoring site", site_id=site_id, url=site_config['homepage'])
            
            # Get homepage
            response = self.session.get(site_config['homepage'], timeout=30)
            response.raise_for_status()
            
            # Parse and extract article links
            soup = BeautifulSoup(response.text, 'html.parser')
            article_links = self.extract_article_links(soup, site_config)
            
            self.logger.info(
                "Found articles", 
                site_id=site_id, 
                count=len(article_links)
            )
            
            # Process each article
            for article_url in article_links:
                await self.process_article(article_url, site_id, site_config)
                await asyncio.sleep(1)  # Be polite between requests
                
        except Exception as e:
            self.logger.error("Error monitoring site", site_id=site_id, error=str(e))
            self.stats['errors'] += 1
    
    def extract_article_links(self, soup: BeautifulSoup, site_config: Dict[str, Any]) -> List[str]:
        """Extract article links from homepage."""
        links = []
        article_pattern = site_config.get('article_pattern')
        
        # Find all links matching the selector
        for link in soup.select(site_config['selectors']['article_links']):
            href = link.get('href')
            if href:
                # Make absolute URL
                absolute_url = urljoin(site_config['homepage'], href)
                
                # Check if it matches article pattern
                if article_pattern and re.search(article_pattern, absolute_url):
                    normalized = normalize_url(absolute_url)
                    if normalized and normalized not in links:
                        links.append(normalized)
        
        return links
    
    async def process_article(self, url: str, site_id: str, site_config: Dict[str, Any]):
        """Process a single article."""
        try:
            self.stats['articles_found'] += 1
            
            # Fetch article
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Extract content
            content = self.extract_article_content(response.text, url, site_id, site_config)
            
            if content:
                # Send to Kafka
                self.send_to_kafka(content)
                self.stats['articles_processed'] += 1
                
                self.logger.info(
                    "Processed article",
                    url=url,
                    title=content.get('title', '')[:100]
                )
            else:
                self.logger.warning("No content extracted", url=url)
                
        except Exception as e:
            self.logger.error("Error processing article", url=url, error=str(e))
            self.stats['errors'] += 1
    
    def extract_article_content(
        self, 
        html: str, 
        url: str, 
        site_id: str, 
        site_config: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Extract content from article page."""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            selectors = site_config['selectors']
            
            # Extract structured data (JSON-LD) first - most reliable
            structured_data = self.extract_structured_data(soup, selectors)
            
            # Try to use JSON-LD data if available and site prefers it
            title = None
            subtitle = None
            content = None
            author = None
            publish_date = None
            
            if site_config.get('use_json_ld', False) and structured_data:
                # Look for NewsArticle in structured data
                for data in structured_data:
                    if isinstance(data, dict) and data.get('@type') == 'NewsArticle':
                        title = data.get('headline')
                        subtitle = data.get('description')
                        content = data.get('articleBody')
                        publish_date = data.get('datePublished')
                        
                        # Extract author from JSON-LD
                        author_data = data.get('author')
                        if isinstance(author_data, dict):
                            author = author_data.get('name')
                        elif isinstance(author_data, list) and author_data:
                            author = author_data[0].get('name') if isinstance(author_data[0], dict) else str(author_data[0])
                        
                        self.logger.debug("Using JSON-LD data", title=title[:50] if title else None)
                        break
            
            # Fallback to HTML selectors if JSON-LD didn't provide everything
            if not title:
                title_selector = selectors.get('title', 'h1')
                if title_selector:
                    title_elem = soup.select_one(title_selector)
                    title = title_elem.get_text(strip=True) if title_elem else None
            
            if not subtitle:
                subtitle_selector = selectors.get('subtitle', 'h2')
                if subtitle_selector:
                    subtitle_elem = soup.select_one(subtitle_selector)
                    subtitle = subtitle_elem.get_text(strip=True) if subtitle_elem else None
            
            if not content:
                # Try content paragraphs first (more specific)
                if selectors.get('content_paragraphs'):
                    paragraphs = soup.select(selectors['content_paragraphs'])
                    if paragraphs:
                        content_parts = []
                        for p in paragraphs:
                            text = p.get_text(strip=True)
                            if text and len(text) > 20:  # Only substantial paragraphs
                                content_parts.append(text)
                        content = '\n\n'.join(content_parts) if content_parts else None
                
                # Fallback to main content container
                if not content:
                    content_selector = selectors.get('content', 'article')
                    if content_selector:
                        content_elem = soup.select_one(content_selector)
                        if content_elem:
                            # Remove script and style tags
                            for tag in content_elem(['script', 'style']):
                                tag.decompose()
                            content = content_elem.get_text(separator='\n', strip=True)
            
            if not author:
                # Try author link first (more specific)
                author_link_selector = selectors.get('author_link')
                if author_link_selector:
                    author_elem = soup.select_one(author_link_selector)
                else:
                    author_elem = None
                
                if not author_elem:
                    author_selector = selectors.get('author')
                    if author_selector:
                        author_elem = soup.select_one(author_selector)
                    else:
                        author_elem = None
                
                if author_elem:
                    author_text = author_elem.get_text(strip=True)
                    # Clean up author text
                    if author_text.startswith('Por'):
                        author = author_text[3:].strip()
                    else:
                        author = author_text
            
            if not publish_date:
                date_selector = selectors.get('date')
                if date_selector:
                    date_elem = soup.select_one(date_selector)
                    if date_elem:
                        if date_elem.name == 'meta':
                            publish_date = date_elem.get('content')
                        elif date_elem.get('datetime'):
                            publish_date = date_elem.get('datetime')
                        else:
                            publish_date = date_elem.get_text(strip=True)
            
            # Extract category from URL or breadcrumbs
            category = self.extract_category(url, soup)
            
            # Extract metadata
            metadata = self.extract_metadata(soup, selectors)
            
            # Only return if we have minimum content
            if title and content and len(content) > 100:
                return {
                    'url': url,
                    'site_id': site_id,
                    'site_name': site_config['name'],
                    'domain': site_config['domain'],
                    'title': title,
                    'subtitle': subtitle,
                    'content': content,
                    'author': author,
                    'publish_date': publish_date,
                    'category': category,
                    'metadata': metadata,
                    'structured_data': structured_data,
                    'timestamp': datetime.utcnow().isoformat(),
                    'crawler_id': 'news-monitor-1',
                    'content_length': len(content),
                    'language': 'es'
                }
            
            return None
            
        except Exception as e:
            self.logger.error("Error extracting content", url=url, error=str(e))
            return None
    
    def extract_category(self, url: str, soup: BeautifulSoup) -> Optional[str]:
        """Extract category from URL or page."""
        # Try to extract from URL path
        path_parts = urlparse(url).path.split('/')
        categories = ['nacional', 'internacional', 'deportes', 'economia', 'tecnologia', 
                     'espectaculos', 'tendencias', 'politica', 'sociedad']
        
        for part in path_parts:
            if part.lower() in categories:
                return part.capitalize()
        
        # Try breadcrumbs
        breadcrumbs = soup.select('nav.breadcrumb a, .breadcrumb a')
        if len(breadcrumbs) > 1:
            return breadcrumbs[1].get_text(strip=True)
        
        return None
    
    def extract_metadata(self, soup: BeautifulSoup, selectors: Dict[str, str]) -> Dict[str, Any]:
        """Extract metadata from HTML head section."""
        metadata = {}
        
        # Helper function to get meta content
        def get_meta_content(selector):
            if selector:
                elem = soup.select_one(selector)
                if elem:
                    return elem.get('content') or elem.get('href') or elem.get_text(strip=True)
            return None
        
        # Helper function to get attribute value
        def get_attribute_value(selector, attribute):
            if selector:
                elem = soup.select_one(selector)
                if elem:
                    return elem.get(attribute)
            return None
        
        # Extract basic metadata
        metadata['meta_title'] = get_meta_content(selectors.get('meta_title', 'title'))
        metadata['meta_description'] = get_meta_content(selectors.get('meta_description'))
        metadata['meta_keywords'] = get_meta_content(selectors.get('meta_keywords'))
        metadata['meta_news_keywords'] = get_meta_content(selectors.get('meta_news_keywords'))
        metadata['meta_author'] = get_meta_content(selectors.get('meta_author'))
        
        # Extract URLs
        metadata['canonical_url'] = get_meta_content(selectors.get('canonical_url', 'link[rel="canonical"]'))
        metadata['amp_url'] = get_meta_content(selectors.get('amp_url'))
        
        # Extract BioBio specific metadata
        metadata['article_id'] = get_meta_content(selectors.get('article_id'))
        metadata['article_section'] = get_meta_content(selectors.get('article_section'))
        metadata['date_published'] = get_meta_content(selectors.get('date_published'))
        metadata['date_modified'] = get_meta_content(selectors.get('date_modified'))
        
        # Extract data attributes
        if selectors.get('data_id_nota'):
            data_id_elem = soup.select_one(selectors['data_id_nota'])
            metadata['data_id_nota'] = data_id_elem.get('data-id-nota') if data_id_elem else None
        
        # Extract Open Graph metadata (extended)
        metadata['open_graph'] = {
            'title': get_meta_content(selectors.get('og_title')),
            'description': get_meta_content(selectors.get('og_description')),
            'image': get_meta_content(selectors.get('og_image')),
            'url': get_meta_content(selectors.get('og_url')),
            'site_name': get_meta_content(selectors.get('og_site_name')),
            'type': get_meta_content(selectors.get('og_type')),
            'article_author': get_meta_content(selectors.get('og_article_author')),
            'article_section': get_meta_content(selectors.get('og_article_section')),
            'article_published_time': get_meta_content(selectors.get('og_article_published_time')),
            'article_modified_time': get_meta_content(selectors.get('og_article_modified_time'))
        }
        
        # Extract Twitter Card metadata (extended)
        metadata['twitter_card'] = {
            'title': get_meta_content(selectors.get('twitter_title')),
            'description': get_meta_content(selectors.get('twitter_description')),
            'image': get_meta_content(selectors.get('twitter_image')),
            'card': get_meta_content(selectors.get('twitter_card')),
            'site': get_meta_content(selectors.get('twitter_site')),
            'creator': get_meta_content(selectors.get('twitter_creator'))
        }
        
        # Extract Facebook specific metadata
        metadata['facebook'] = {
            'pages': get_meta_content(selectors.get('fb_pages')),
            'app_id': get_meta_content(selectors.get('fb_app_id')),
            'admins': get_meta_content(selectors.get('fb_admins'))
        }
        
        # Extract favicon and icons
        metadata['icons'] = {
            'favicon': get_meta_content(selectors.get('favicon')),
            'apple_touch_icon': get_meta_content(selectors.get('apple_touch_icon'))
        }
        
        # Extract BioBio specific content elements
        biobio_elements = {}
        if selectors.get('destacador'):
            destacador_elems = soup.select(selectors['destacador'])
            biobio_elements['destacadores'] = [elem.get_text(strip=True) for elem in destacador_elems]
        
        if selectors.get('lee_tambien'):
            lee_tambien_elems = soup.select(selectors['lee_tambien'])
            biobio_elements['lee_tambien'] = [elem.get_text(strip=True) for elem in lee_tambien_elems]
        
        if selectors.get('wp_caption'):
            caption_elems = soup.select(selectors['wp_caption'])
            biobio_elements['image_captions'] = [elem.get_text(strip=True) for elem in caption_elems]
        
        if selectors.get('audio_elements'):
            audio_elems = soup.select(selectors['audio_elements'])
            biobio_elements['audio_count'] = len(audio_elems)
            biobio_elements['audio_ids'] = [elem.get('id') for elem in audio_elems if elem.get('id')]
        
        if biobio_elements:
            metadata['biobio_elements'] = biobio_elements
        
        # Remove None values to keep data clean
        def clean_dict(d):
            if isinstance(d, dict):
                return {k: clean_dict(v) for k, v in d.items() if v is not None and v != {}}
            return d
        
        metadata = clean_dict(metadata)
        
        return metadata
    
    def extract_structured_data(self, soup: BeautifulSoup, selectors: Dict[str, str]) -> List[Dict[str, Any]]:
        """Extract JSON-LD structured data."""
        structured_data = []
        
        # Find all JSON-LD scripts
        json_ld_selector = selectors.get('json_ld', 'script[type="application/ld+json"]')
        json_scripts = soup.select(json_ld_selector)
        
        for script in json_scripts:
            try:
                json_content = script.get_text(strip=True)
                if json_content:
                    data = json.loads(json_content)
                    structured_data.append(data)
                    
                    # Log important structured data types
                    if isinstance(data, dict):
                        data_type = data.get('@type')
                        if data_type:
                            self.logger.debug("Found structured data", type=data_type)
                            
            except json.JSONDecodeError as e:
                self.logger.warning("Invalid JSON-LD found", error=str(e))
                continue
        
        return structured_data
    
    def send_to_kafka(self, content: Dict[str, Any]):
        """Send article content to Kafka."""
        if not self.kafka_enabled or not self.kafka_producer:
            self.logger.debug("Kafka disabled, skipping send", url=content['url'])
            return
            
        try:
            topic = 'news_content'
            key = content['site_id']
            
            self.kafka_producer.send(topic, value=content, key=key)
            self.kafka_producer.flush()  # Ensure it's sent
            
            self.logger.debug(
                "Sent to Kafka",
                topic=topic,
                url=content['url'],
                title=content['title'][:50]
            )
            
        except Exception as e:
            self.logger.error("Failed to send to Kafka", error=str(e))
    
    def get_stats(self) -> Dict[str, Any]:
        """Get monitor statistics."""
        runtime = (datetime.utcnow() - self.stats['start_time']).total_seconds()
        return {
            **self.stats,
            'runtime_seconds': runtime,
            'articles_per_minute': self.stats['articles_processed'] / (runtime / 60) if runtime > 0 else 0
        }


def main():
    """Main entry point."""
    monitor = NewsMonitor()
    asyncio.run(monitor.start())


if __name__ == '__main__':
    main() 