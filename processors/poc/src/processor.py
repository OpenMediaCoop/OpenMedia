from selectolax.parser import HTMLParser
from models import NewsInput, ScrapingMetadataInput
import datetime

def parse_html(raw_html: str) -> NewsInput:
    tree = HTMLParser(raw_html)
    
    title = tree.css_first("title").text(strip=True) if tree.css_first("title") else "Sin título"
    body_text = tree.body.text(strip=True)[:4000] if tree.body else ""

    return NewsInput(
        title=title,
        content=body_text,
        published_at=datetime.datetime.now(datetime.timezone.utc),
    )