import asyncio

import httpx


API_URL = "http://127.0.0.1:8000/reservations"


async def make_request(client: httpx.AsyncClient, request_number: int):
    response = await client.post(
        API_URL,
        json={
            "seat_id": 999,
            "user_id": f"admission-user-{request_number}",
        },
    )

    return response.status_code


async def main():
    async with httpx.AsyncClient() as client:
        tasks = [
            make_request(client, number)
            for number in range(100)
        ]

        results = await asyncio.gather(*tasks)

    admitted = sum(
        1 for status in results
        if status != 503
    )

    rejected = sum(
        1 for status in results
        if status == 503
    )

    print("Admitted:", admitted)
    print("Rejected by admission control:", rejected)


if __name__ == "__main__":
    asyncio.run(main())