from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db


router = APIRouter(
    prefix="/reservations",
    tags=["reservations"],
)

class ReservationRequest(BaseModel):
    seat_id: int
    user_id: str

@router.post("")
async def create_reservation(
    request: ReservationRequest,
    db: AsyncSession = Depends(get_db),
):
    reservation_id = uuid4()

    async with db.begin():
        seat_result = await db.execute(
            text(
                """
                UPDATE seats
                SET
                    status = 'RESERVED',
                    reserved_by = :user_id,
                    reservation_expires_at = NOW() + INTERVAL '5 minutes'
                WHERE id = :seat_id
                  AND status = 'AVAILABLE'
                RETURNING
                    id,
                    reservation_expires_at;
                """
            ),
            {
                "seat_id": request.seat_id,
                "user_id": request.user_id,
            },
        )

        seat = seat_result.mappings().one_or_none()

        if seat is None:
            raise HTTPException(
                status_code=409,
                detail="Seat is unavailable",
            )

        await db.execute(
            text(
                """
                INSERT INTO reservations (
                    id,
                    seat_id,
                    user_id,
                    status,
                    expires_at
                )
                VALUES (
                    :reservation_id,
                    :seat_id,
                    :user_id,
                    'ACTIVE',
                    :expires_at
                );
                """
            ),
            {
                "reservation_id": reservation_id,
                "seat_id": request.seat_id,
                "user_id": request.user_id,
                "expires_at": seat["reservation_expires_at"],
            },
        )

    return {
        "reservation_id": str(reservation_id),
        "seat_id": request.seat_id,
        "user_id": request.user_id,
        "status": "ACTIVE",
        "expires_at": seat["reservation_expires_at"],
    }