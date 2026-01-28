import json
import asyncio
import os
from aiokafka import AIOKafkaConsumer

from application.use_cases.send_notification import SendNotification
from application.use_cases.process_events import (
    ProcessExamScheduledEvent,
    ProcessAnomalyDetectedEvent,
    ProcessGradingCompletedEvent,
    ProcessHighRiskAlertEvent
)


class KafkaEventConsumer:
    TOPICS = [
        "exam_scheduled",
        "anomaly_detected",
        "grading_completed",
        "high_risk_alert"
    ]

    def __init__(
        self,
        send_notification: SendNotification,
        bootstrap_servers: str = None,
        group_id: str = "notification-service"
    ):
        self.bootstrap_servers = bootstrap_servers or os.getenv(
            "KAFKA_BOOTSTRAP_SERVERS",
            "localhost:9092"
        )
        self.group_id = group_id
        self.consumer = None

        self.exam_scheduled_handler = ProcessExamScheduledEvent(send_notification)
        self.anomaly_handler = ProcessAnomalyDetectedEvent(send_notification)
        self.grading_handler = ProcessGradingCompletedEvent(send_notification)
        self.high_risk_handler = ProcessHighRiskAlertEvent(send_notification)

    async def start(self):
        self.consumer = AIOKafkaConsumer(
            *self.TOPICS,
            bootstrap_servers=self.bootstrap_servers,
            group_id=self.group_id,
            auto_offset_reset="latest"
        )
        await self.consumer.start()
        print(f"Kafka consumer started, listening to topics: {self.TOPICS}")

    async def stop(self):
        if self.consumer:
            await self.consumer.stop()
            print("Kafka consumer stopped")

    async def consume(self):
        try:
            async for message in self.consumer:
                topic = message.topic
                try:
                    event = json.loads(message.value.decode('utf-8'))
                    await self._handle_event(topic, event)
                except Exception as e:
                    print(f"Error processing message from {topic}: {e}")
        except asyncio.CancelledError:
            pass

    async def _handle_event(self, topic: str, event: dict):
        print(f"Processing event from topic {topic}: {event.get('user_id', 'unknown')}")

        if topic == "exam_scheduled":
            await self.exam_scheduled_handler.execute(event)
        elif topic == "anomaly_detected":
            await self.anomaly_handler.execute(event)
        elif topic == "grading_completed":
            await self.grading_handler.execute(event)
        elif topic == "high_risk_alert":
            await self.high_risk_handler.execute(event)
        else:
            print(f"Unknown topic: {topic}")
