import json
import logging
from aiokafka import AIOKafkaConsumer

logger = logging.getLogger(__name__)

async def create_consumer(
    topic: str,
    bootstrap_servers: str,
    group_id: str,
    handle_message_fn,
    auto_offset_reset: str = "earliest",
    enable_auto_commit: bool = True,
):
    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=bootstrap_servers,
        group_id=group_id,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset=auto_offset_reset,
        enable_auto_commit=enable_auto_commit,
    )
    await consumer.start()
    logger.info(f"🟢 Escuchando tópico: {topic}")
    try:
        async for msg in consumer:
            await handle_message_fn(msg.value)
    finally:
        await consumer.stop()