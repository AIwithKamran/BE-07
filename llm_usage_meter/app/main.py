from contextlib import asynccontextmanager
from fastapi import FastAPI
from core.database import engine, Base

from models.plan import Plan
from models.tenant import Tenant
from models.subscriptions import Subscriptions
from models.usage_event import UsageEvent

from api.usage import router as usage_router
from api.payment import router as payment_router

@asynccontextmanager
async def lifespan(app):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(title="Usage Metering & Billing Engine", lifespan=lifespan)

app.include_router(usage_router)
app.include_router(payment_router)

@app.get("/")
async def root():
    return {"message": "Usage Metering & Billing Engine is running"}
