import os
from dotenv import load_dotenv

load_dotenv()

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "raw-html")

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "htmlparser")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "documents")

PGVECTOR_DSN = os.getenv("PGVECTOR_DSN", "postgresql://user:password@localhost:5432/dbname")