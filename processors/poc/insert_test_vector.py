
from kafka import KafkaProducer
import json
import uuid

producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

test_html = """
<html>
  <head><title>Corrupción Municipal en Ñuñoa</title></head>
  <body>
    <article>
      <h1>Millonario desfalco detectado en la municipalidad</h1>
      <p>Según informes, se desviaron fondos a campañas políticas entre 2020 y 2022.</p>
      <p>La fiscalía abrió una investigación y detuvo a 3 funcionarios.</p>
      <footer>Publicado en El Diario de Chile</footer>
    </article>
  </body>
</html>
"""

payload = {
    "id": str(uuid.uuid4()),
    "title": "Corrupción en Ñuñoa",
    "content": test_html,
    "published_at": "2023-05-01T12:30:00Z",
    "fuente": "El Diario de Chile"
}

producer.send("vector.topic", value=payload)
producer.flush()

print("Mensaje enviado a Kafka")