from fastapi import FastAPI
from sqlalchemy import text

from app.core.database import engine
from app.api.events import router as events_router
from app.api.reservations import router as reservations_router
from app.api.orders import router as orders_router

app = FastAPI(
    title="Autoscaling Ticket Reservation Platform"
)

app.include_router(events_router)
app.include_router(reservations_router)
app.include_router(orders_router)

@app.get("/health")
async def health() -> dict[str, str]:
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))
    
    return {"status": "ok",
            "service": "booking api",
            "database": "connected",
            } 

@app.get("/livez")
async def livez():
    return {"status": "alive"}


@app.get("/readyz")
async def readyz():
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))

    return {
        "status": "ready",
        "database": "connected",
    }