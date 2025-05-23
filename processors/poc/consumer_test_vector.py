from kafka import KafkaConsumer
import json

consumer = KafkaConsumer(
    "vector.topic",
    bootstrap_servers="localhost:9092",
    auto_offset_reset="earliest",  # lee desde el principio del topic
    enable_auto_commit=True,
    group_id="debug-consumer",
    value_deserializer=lambda m: json.loads(m.decode("utf-8"))
)

print("🟢 Esperando mensajes en 'vector.topic'...")

try:
    for message in consumer:
        print("🟢 Mensaje recibido:")
        print(f"  ID: {message.value.get('id')}")
        print(f"  Title: {message.value.get('title')}")
        print(f"  Publicado: {message.value.get('published_at')}")
        print(f"  HTML preview:\n{message.value.get('content')[:300]}")
        print("—" * 60)
except KeyboardInterrupt:
    print("\n🔴 Cancelado por el usuario")