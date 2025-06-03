import os
from dotenv import load_dotenv

load_dotenv()

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "raw-html")

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "htmlparser")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "documents")

PGVECTOR_DSN = os.getenv("PGVECTOR_DSN", "postgresql+asyncpg://postgres:postgres@localhost:5432/news_db")

print(f"Using Kafka bootstrap servers: {KAFKA_BOOTSTRAP_SERVERS}")
print(f"Using PgVector DSN: {PGVECTOR_DSN}")