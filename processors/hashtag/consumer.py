import asyncio
import logging
from common.kafka.conssumer import create_consumer
from .handler import handle_message
from common.config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC

GROUP_ID = "hashtag-processor-group"

logging.basicConfig(level=logging.INFO)

async def consume():
    return await create_consumer(
        topic=KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id=GROUP_ID,
        handle_message_fn=handle_message,
    )
