from fastapi import FastAPI
from sqlalchemy import text

from app.core.database import engine
from app.api.events import router as events_router

app = FastAPI(
    title="Autoscaling Ticket Reservation Platform"
)

app.include_router(events_router)

@app.get("/health")
async def health() -> dict[str, str]:
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))
    
    return {"status": "ok",
            "service": "booking api",
            "database": "connected",
            } 