import asyncio
import httpx

API_URL = "http://127.0.0.1:8000/reservations"

RESERVATION_ID = "6ce9239b-49ce-404a-9794-413f3800b0cd"

async def make_request(client: httpx.AsyncClient, request_number: int):
    response = await client.post(
        API_URL,
        json={
            "seat_id": 999,
            "user_id": "rate-limit-user"
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
            make_request(client, request_number)
            for request_number in range(20)
        ]

        results = await asyncio.gather(*tasks)

    allowed = 0
    rate_limited = 0

    for request_number, status_code, body in results:
        if status_code == 429:
            rate_limited += 1
        else:
            allowed += 1
        print(request_number, status_code, body)

    print("Allowed:", allowed)
    print("Rate limited:", rate_limited)

if __name__ == "__main__":
    asyncio.run(main())