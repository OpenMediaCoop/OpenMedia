import json
import logging
from aiokafka import AIOKafkaConsumer

logger = logging.getLogger(__name__)

def safe_deserializer(m: bytes) -> dict:
    try:
        decoded = m.decode("utf-8").strip()
        return json.loads(decoded)
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        logger.warning(f"Mensaje descartado por error de formato: {e} - contenido: {m!r}")
        return None  # Devuelve None para que tu lógica pueda ignorarlo


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
        value_deserializer=safe_deserializer,
        auto_offset_reset=auto_offset_reset,
        enable_auto_commit=enable_auto_commit,
    )
    await consumer.start()
    logger.info(f"🟢 Escuchando tópico: {topic}")

    try:
        async for msg in consumer:
            if msg.value is None:
                logger.warning("Mensaje recibido con valor None, se ignorará.")
                continue
            await handle_message_fn(msg.value)
    finally:
        await consumer.stop()