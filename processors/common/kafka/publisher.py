

import json
import logging
from aiokafka import AIOKafkaProducer

logger = logging.getLogger(__name__)

class KafkaPublisher:
    def __init__(self, bootstrap_servers: str = "kafka:9092"):
        self.bootstrap_servers = bootstrap_servers
        self.producer = None

    async def start(self):
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8")
        )
        await self.producer.start()
        logger.info("🟢 Publisher Kafka iniciado.")

    async def stop(self):
        if self.producer:
            await self.producer.stop()
            logger.info("🔴 Publisher Kafka detenido.")

    async def publish(self, topic: str, message: dict):
        if not self.producer:
            raise RuntimeError("KafkaPublisher no está inicializado. Llama a start() primero.")
        await self.producer.send_and_wait(topic, message)
        logger.info(f"📤 Mensaje publicado en {topic}: {message.get('id', 'sin id')}")