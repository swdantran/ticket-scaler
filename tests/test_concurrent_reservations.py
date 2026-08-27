import asyncio

import httpx


API_URL = "http://127.0.0.1:8000/reservations"


async def reserve_seat(client: httpx.AsyncClient, user_number: int):
    response = await client.post(
        API_URL,
        json={
            "seat_id": 1,
            "user_id": f"user-{user_number}",
        },
    )

    return response.status_code, response.json()


async def main():
    async with httpx.AsyncClient() as client:
        tasks = [
            reserve_seat(client, user_number)
            for user_number in range(100)
        ]

        results = await asyncio.gather(*tasks)

    success_count = 0
    conflict_count = 0

    for status_code, body in results:
        if status_code == 200:
            success_count += 1
        elif status_code == 409:
            conflict_count += 1
        else:
            print("Unexpected response:", status_code, body)

    print("Successful reservations:", success_count)
    print("Rejected reservations:", conflict_count)


if __name__ == "__main__":
    asyncio.run(main())