import json
from aiokafka import AIOKafkaProducer

from app.core.config import settings

async def publish_order_confirmed(order: dict):
    producer = AIOKafkaProducer(
        bootstrap_servers=settings.kafka_bootstrap_servers,
    )

    await producer.start()

    try:
        await producer.send_and_wait(
            "order-confirmed",
            json.dumps(order).encode("utf-8"),
        )
    finally:
        await producer.stop()
