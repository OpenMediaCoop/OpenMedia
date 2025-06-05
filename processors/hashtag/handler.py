import asyncio
import logging
from .processor import HashtagProcessor

logger = logging.getLogger(__name__)

async def handle_message(message: dict):
    message_id = message.get('id', '[sin id]')
    logger.info(f"📥 Recibido mensaje ID={message_id} | Título: {message.get('title', '')[:40]}")
    processor = HashtagProcessor()
    try:
        await processor.process(message)
        logger.info(f"✅ Procesado mensaje ID={message_id}")
    except Exception as e:
        logger.exception(f"❌ Error al procesar mensaje ID={message_id}: {e}")