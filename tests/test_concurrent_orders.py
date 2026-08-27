import asyncio
import httpx

API_URL = "http://127.0.0.1:8000/orders"

RESERVATION_ID = "6cdfa74a-01d4-4fd4-a9ae-5dd5011adeb4"

async def checkout(client: httpx.AsyncClient, request_number: int):
    response = await client.post(
        API_URL,
        json={
            "reservation_id": RESERVATION_ID,
            "user_id": "concurrent-user",
            "idempotency_key": "concurrent-checkout-001",
        },
    )

    return (
        request_number,
        response.status_code,
        response.json(),
    )