import json
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

router = APIRouter(
    prefix="/orders",
    tags=["orders"],
)

class OrderRequest(BaseModel):
    reservation_id: str
    user_id: str
    idempotency_key: str

async def get_database_time(db: AsyncSession):
    result = await db.execute(
        text("SELECT NOW();")
    )

    return result.scalar_one()

@router.post("", status_code=201)
async def create_order(
    request: OrderRequest,
    db: AsyncSession = Depends(get_db),
):
    order_id = uuid4()
    async with db.begin():
        existing_order_result = await db.execute(
            text(
                """
                SELECT
                    id,
                    user_id,
                    reservation_id,
                    idempotency_key,
                    status,
                    created_at
                FROM orders
                WHERE idempotency_key = :idempotency_key;
                """
            ),
            {
                "idempotency_key": request.idempotency_key,
            },
        )

        existing_order = existing_order_result.mappings().one_or_none()

        if existing_order is not None:
            return dict(existing_order)
        
        reservation_result = await db.execute(
            text(
                """
                SELECT
                    id,
                    seat_id,
                    user_id,
                    status,
                    expires_at
                FROM reservations
                WHERE id = :reservation_id
                FOR UPDATE;
                """
            ),
            {
                "reservation_id": request.reservation_id,
            },
        )

        reservation = reservation_result.mappings().one_or_none()

        if reservation is None:
            raise HTTPException(
                status_code=404,
                detail="Reservation not found",
            )

        if reservation["user_id"] != request.user_id:
            raise HTTPException(
                status_code=403,
                detail="Reservation does not belong to this user",
            )

        if reservation["status"] != "ACTIVE":
            raise HTTPException(
                status_code=409,
                detail="Reservation is not active",
            )

        database_time = await get_database_time(db)

        if reservation["expires_at"] <= database_time:
            raise HTTPException(
                status_code=409,
                detail="Reservation has expired",
            )

        await db.execute(
            text(
                """
                INSERT INTO orders (
                    id,
                    user_id,
                    reservation_id,
                    idempotency_key,
                    status
                )
                VALUES (
                    :order_id,
                    :user_id,
                    :reservation_id,
                    :idempotency_key,
                    'CONFIRMED'
                );
                """
            ),
            {
                "order_id": order_id,
                "user_id": request.user_id,
                "reservation_id": request.reservation_id,
                "idempotency_key": request.idempotency_key,
            },
        )

        outbox_event_id = uuid4()

        await db.execute(
            text(
                """
                INSERT INTO outbox_events (
                    id,
                    event_type,
                    payload
                )
                VALUES (
                    :id,
                    :event_type,
                    CAST(:payload AS JSONB)
                );
                """
            ),
            {
                "id": outbox_event_id,
                "event_type": "order.confirmed",
                "payload": json.dumps(
                    {
                        "event_id": str(outbox_event_id),
                        "order_id": str(order_id),
                        "user_id": request.user_id,
                        "reservation_id": request.reservation_id,
                    }
                ),
            },
        )

        await db.execute(
            text(
                """
                UPDATE reservations
                SET status = 'COMPLETED'
                WHERE id = :reservation_id;
                """
            ),
            {
                "reservation_id": request.reservation_id,
            },
        )

        await db.execute(
            text(
                """
                UPDATE seats
                SET
                    status = 'PURCHASED',
                    reservation_expires_at = NULL
                WHERE id = :seat_id;
                """
            ),
            {
                "seat_id": reservation["seat_id"],
            },
        )

    return {
        "id": str(order_id),
        "user_id": request.user_id,
        "reservation_id": request.reservation_id,
        "idempotency_key": request.idempotency_key,
        "status": "CONFIRMED",
    }