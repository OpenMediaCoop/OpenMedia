from selectolax.parser import HTMLParser
from models import HtmlDocument, HtmlMetadata
from datetime import datetime

def parse_html(raw_html: str) -> HtmlDocument:
    tree = HTMLParser(raw_html)
    
    title = tree.css_first("title").text(strip=True) if tree.css_first("title") else "Sin título"
    body_text = tree.body.text(strip=True)[:300] if tree.body else ""

    metadata = HtmlMetadata(
        title=title,
        preview=body_text,
        timestamp=datetime.utcnow()
    )

    return HtmlDocument(html=raw_html, metadata=metadata)