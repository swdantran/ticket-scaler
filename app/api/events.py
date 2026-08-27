from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db


router = APIRouter(
    prefix="/events",
    tags=["events"],
)


@router.get("")
async def list_events(
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text(
            """
            SELECT
                id,
                name,
                venue,
                starts_at,
                created_at
            FROM events
            ORDER BY starts_at;
            """
        )
    )

    events = result.mappings().all()

    return events

@router.get("/{event_id}/seats")
async def list_event_seats(
    event_id: int,
    db: AsyncSession = Depends(get_db)
):
    event_result = await db.execute(
        text(
            """
            SELECT id
            FROM events
            WHERE id = :event_id;
            """
        ),
        {
            "event_id": event_id,
        },
    )

    event = event_result.scalar_one_or_none()

    if event is None:
        raise HTTPException(
            status_code=404,
            detail="Event not found",
        )

    seat_result = await db.execute(
        text(
            """
            SELECT
                id,
                event_id,
                section,
                seat_number,
                price_cents,
                status,
                reserved_by,
                reservation_expires_at
            FROM seats
            WHERE event_id = :event_id
            ORDER BY section, seat_number;
            """
        ),
        {
            "event_id": event_id,
        },
    )

    seats = seat_result.mappings().all()

    return seats