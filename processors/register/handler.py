import asyncio
import logging
from .processor import RegisterProcessor
from common.kafka.publisher import KafkaPublisher

logger = logging.getLogger(__name__)
publisher = KafkaPublisher()

async def handle_message(message: dict):
    logger.info(f"Recibido mensaje: {message.get('id', '[sin id]')}")

    processor = RegisterProcessor()
    result = await processor.process(message)

    await publisher.start()
    await publisher.publish("enrichment.topic", {
        "id": result.id,
        "title": result.title,
        "published_at": result.published_at.isoformat(),
        "source": result.source,
        "url": result.url,
        "content": result.content,
    })
    await publisher.stop()