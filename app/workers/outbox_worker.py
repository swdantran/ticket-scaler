import asyncio
import json

from sqlalchemy import text

from app.core.database import SessionLocal
from app.messaging.producer import publish_order_confirmed


POLL_INTERVAL_SECONDS = 1


async def process_outbox():
    async with SessionLocal() as db:
        async with db.begin():
            result = await db.execute(
                text(
                    """
                    SELECT
                        id,
                        event_type,
                        payload
                    FROM outbox_events
                    WHERE processed = FALSE
                    ORDER BY created_at
                    LIMIT 10
                    FOR UPDATE SKIP LOCKED;
                    """
                )
            )

            events = result.mappings().all()

            for event in events:
                payload = event["payload"]

                if isinstance(payload, str):
                    payload = json.loads(payload)

                if event["event_type"] == "order.confirmed":
                    await publish_order_confirmed(payload)

                await db.execute(
                    text(
                        """
                        UPDATE outbox_events
                        SET processed = TRUE
                        WHERE id = :event_id;
                        """
                    ),
                    {
                        "event_id": event["id"],
                    },
                )


async def main():
    while True:
        try:
            await process_outbox()

        except Exception as error:
            print("Outbox worker error:", error)

        await asyncio.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    asyncio.run(main())