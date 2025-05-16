from aiokafka import AIOKafkaProducer
import asyncio
import json

class KafkaEventPublisher:
    def __init__(self, bootstrap_servers):
        self.bootstrap_servers = bootstrap_servers
        self.producer = None

    async def start(self):
        self.producer = AIOKafkaProducer(bootstrap_servers=self.bootstrap_servers)
        await self.producer.start()

    async def stop(self):
        if self.producer:
            await self.producer.stop()

    async def publish(self, topic: str, message: dict):
        if not self.producer:
            await self.start()
        await self.producer.send_and_wait(topic, json.dumps(message).encode('utf-8'))
