import asyncio
import logging
from common.kafka.conssumer import create_consumer
from .handler import handle_message

KAFKA_TOPIC = "enrichment.topic"
KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
GROUP_ID = "vector-processor-group"

logging.basicConfig(level=logging.INFO)

async def consume():
    return await create_consumer(
        topic=KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id=GROUP_ID,
        handle_message_fn=handle_message,
    )
