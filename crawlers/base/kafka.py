from kafka import KafkaProducer
from typing import Dict, Any
from base.utils import get_config
from base.logger import logger
import json

def init_kafka():
    """Initialize Kafka producer."""
    try:
        kafka_config = get_config().get('kafka', {})
        return KafkaProducer(
            bootstrap_servers=kafka_config.get('bootstrap_servers', 'kafka:9092'),
            value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None
        )
    except Exception as e:
        logger.warning("Failed to initialize Kafka, running without it", error=str(e))
    

def send_to_kafka(content: Dict[str, Any]):
        """Send article content to Kafka."""
        if not kafka_producer:
            logger.debug("Kafka disabled, skipping send", url=content['url'])
            return
        try:
            topic = 'news_content'
            key = content['site_id']
            
            kafka_producer.send(topic, value=content, key=key)
            kafka_producer.flush()  # Ensure it's sent
            
            logger.debug(
                "Sent to Kafka",
                topic=topic,
                url=content['url'],
                title=content['title'][:50]
            )
            
        except Exception as e:
            logger.error("Failed to send to Kafka", error=str(e))

kafka_producer = init_kafka()