

import asyncio
import json
import logging
from aiokafka import AIOKafkaConsumer
from .handler import handle_message

KAFKA_TOPIC = "vector.topic"
KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
GROUP_ID = "vector-processor-group"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def consume():
    consumer = AIOKafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id=GROUP_ID,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="earliest",
        enable_auto_commit=True,
    )
    await consumer.start()
    try:
        logger.info(f"Escuchando tópico: {KAFKA_TOPIC}")
        async for msg in consumer:
            await handle_message(msg.value)
    finally:
        await consumer.stop()

if __name__ == "__main__":
    asyncio.run(consume())