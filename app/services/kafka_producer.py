import json
from confluent_kafka import Producer
from app.core.config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC

class KafkaProducerService:

    def __init__(self):
        # Configuration for the Kafka Producer
        conf = {'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS}
        self.producer = Producer(conf)

    def delivery_report(self, err, msg):

        if err is not None:
            print(f"Message delivery failed: {err}")

    def produce_position_changed_event(self, event_data: dict):

        payload = json.dumps(event_data)
        self.producer.poll(0)
        self.producer.produce(topic=KAFKA_TOPIC, value=payload, callback=self.delivery_report)

    def flush(self):
        self.producer.flush()