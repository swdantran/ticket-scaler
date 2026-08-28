import asyncio
import json

from aiokafka import AIOKafkaConsumer
from sqlalchemy import text

from app.core.config import settings
from app.core.database import SessionLocal

async def process_event(event: dict):
    event_id = event["event_id"]

    if event_id is None:
        print("Skipping legacy event without event_id:", event)
        return

    async with SessionLocal() as db:
        async with db.begin():

            result = await db.execute(
                text(
                    """
                    SELECT event_id
                    FROM processed_events
                    WHERE event_id = :event_id;
                    """
                ),
                {
                    "event_id": event_id,
                },
            )

            already_processed = result.first()

            if already_processed:
                print(f"Skipping duplicate event: {event_id}")
                return

            print("Processing order:")
            print(event)
           
            await db.execute(
                text(
                    """
                    INSERT INTO processed_events (event_id)
                    VALUES (:event_id);
                    """
                ),
                {
                    "event_id": event_id,
                },
            )


async def main():
    consumer = AIOKafkaConsumer(
        "order-confirmed",
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id="order-workers",
        auto_offset_reset="earliest",
        enable_auto_commit=True,
    )

    await consumer.start()

    try:
        print("Order consumer started")

        async for message in consumer:
            event = json.loads(message.value.decode("utf-8"))

            try:
                await process_event(event)

            except Exception as error:
                print("failed to process event:", error)
    
    finally:
        await consumer.stop()


if __name__ == "__main__":
    asyncio.run(main())