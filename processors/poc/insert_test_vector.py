from kafka import KafkaProducer
import json
import uuid

# producer = KafkaProducer(
#     bootstrap_servers="localhost:9092",
#     value_serializer=lambda v: json.dumps(v).encode("utf-8")
# )
# print("🟡 KafkaProducer creado en localhost:9092")

test_html = """
<html>
  <head>
    <title>Corrupción Municipal en Ñuñoa</title>
    <meta name="author" content="El Diario de Chile">
  </head>
  <body>
    <article>
      <h1>Millonario desfalco detectado en la municipalidad</h1>
      <p>Según informes, se desviaron fondos a campañas políticas entre 2020 y 2022.</p>
      <p>La fiscalía abrió una investigación y detuvo a 3 funcionarios.</p>
      <time datetime="2023-05-01T12:30:00Z">1 de mayo de 2023</time>
      <footer>Publicado en El Diario de Chile</footer>
    </article>
  </body>
</html>
"""

payload = {
    "id": str(uuid.uuid4()),
    "html": test_html
}

print("🟢 Enviando mensaje a topic 'vector.topic'...")
print("payload:", payload)
# producer.send("vector.topic", value=payload)
# producer.flush()

print(f"✅ Mensaje enviado a Kafka con ID: {payload['id']}")