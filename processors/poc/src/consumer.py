from aiokafka import AIOKafkaConsumer
from config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC
from processor import parse_html
from storage import PgVectorStorage
import asyncio

async def consume_and_process():
    consumer = AIOKafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id="vector-topic-consumer",
        auto_offset_reset="earliest",
        enable_auto_commit=True
    )
    print(f"🟡 Iniciando conexión a Kafka en: {KAFKA_BOOTSTRAP_SERVERS}")
    try:
        await consumer.start()
        print("🟢 Conectado a Kafka y esperando mensajes…")
    except Exception as e:
        print(f"🔴 Error al conectar con Kafka: {e}")
        return
    storage = PgVectorStorage()
    await storage.connect()

    try:
        async for msg in consumer:
            print("🟢 Mensaje recibido de Kafka")
            raw_html = msg.value.decode("utf-8")
            print("Contenido:", raw_html[:200])
            doc = parse_html(raw_html)
            inserted_id = await storage.insert_news(doc)
            print(f"✔ Guardado en PostgreSQL con ID: {inserted_id}")
    except Exception as e:
        print(f"❌ ERROR en el loop de consumo: {e}")
    finally:
        await consumer.stop()