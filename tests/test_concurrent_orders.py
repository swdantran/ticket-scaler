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

async def main():
    async with httpx.AsyncClient() as client:
        tasks = [
            checkout(client, request_number)
            for request_number in range(100)
        ]

        results = await asyncio.gather(*tasks)

    success_count = 0
    errors = 0

    for request_number, status_code, body in results:
        if status_code in (200, 201):
            succes_count += 1
        else:
            errors += 1
            print("Unexpected:", request_number, status_code, body)

    print("Successful respons:", success_count)
    print("Unexpected responses:", errors)

if __name__ == "__main__":
    asyncio.run(main())