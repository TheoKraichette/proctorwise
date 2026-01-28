import asyncio
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI

from interface.api.controllers import notification_controller
from application.use_cases.send_notification import SendNotification
from infrastructure.repositories.sqlalchemy_notification_repository import SQLAlchemyNotificationRepository
from infrastructure.email.smtp_email_sender import MockEmailSender, SMTPEmailSender
from infrastructure.push.websocket_sender import WebSocketSender, MockRealtimeSender
from infrastructure.events.kafka_consumer import KafkaEventConsumer

consumer_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global consumer_task

    repo = SQLAlchemyNotificationRepository()

    if os.getenv("USE_MOCK_SENDERS", "true").lower() == "true":
        email_sender = MockEmailSender()
        realtime_sender = MockRealtimeSender()
    else:
        email_sender = SMTPEmailSender()
        realtime_sender = WebSocketSender()

    send_notification = SendNotification(repo, email_sender, realtime_sender)
    kafka_consumer = KafkaEventConsumer(send_notification)

    if os.getenv("ENABLE_KAFKA_CONSUMER", "false").lower() == "true":
        await kafka_consumer.start()
        consumer_task = asyncio.create_task(kafka_consumer.consume())

    yield

    if consumer_task:
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass
        await kafka_consumer.stop()


app = FastAPI(
    title="ProctorWise Notification Service",
    description="Email and WebSocket notification service with Kafka event processing",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(notification_controller.router)


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "notification"}
