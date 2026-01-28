import json
from aiokafka import AIOKafkaProducer
from application.interfaces.event_publisher import EventPublisher


class KafkaEventPublisher(EventPublisher):
    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self.producer = None

    async def start(self):
        self.producer = AIOKafkaProducer(bootstrap_servers=self.bootstrap_servers)
        await self.producer.start()

    async def stop(self):
        if self.producer:
            await self.producer.stop()

    async def publish(self, topic: str, message: dict) -> None:
        if not self.producer:
            await self.start()
        await self.producer.send_and_wait(topic, json.dumps(message).encode('utf-8'))
