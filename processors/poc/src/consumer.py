from aiokafka import AIOKafkaConsumer
from config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC
from processor import parse_html
from storage import MongoStorage
import asyncio

async def consume_and_process():
    consumer = AIOKafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id="html-processors"
    )
    await consumer.start()
    storage = MongoStorage()

    try:
        async for msg in consumer:
            raw_html = msg.value.decode("utf-8")
            doc = parse_html(raw_html)
            await storage.insert_document(doc)
            print(f"✔ Guardado: {doc.metadata.title}")
    finally:
        await consumer.stop()