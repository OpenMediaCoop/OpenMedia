import asyncio
import logging
from .processor import VectorProcessor
from .embeddings import generate_embedding

logger = logging.getLogger(__name__)

async def handle_message(message: dict):
    logger.info(f"Recibido mensaje: {message.get('id', '[sin id]')}")
    processor = VectorProcessor()
    await processor.process(message)