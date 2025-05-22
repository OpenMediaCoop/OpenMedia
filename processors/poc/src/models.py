from pydantic import BaseModel
from datetime import datetime

class HtmlMetadata(BaseModel):
    title: str
    preview: str
    timestamp: datetime

class HtmlDocument(BaseModel):
    html: str
    metadata: HtmlMetadata