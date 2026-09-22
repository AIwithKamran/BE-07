import asyncio
from core.database import async_session, engine, Base
from models.subscriptions import Subscriptions
from models.plan import Plan
from models.tenant import Tenant
from models.usage_event import UsageEvent



async def seed():
    # Drop all tables and recreate (fresh start)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        plans = [
           Plan(name="free", api_calls=1000, monthly_tokens=100000),
           Plan(name="pro", api_calls=10000, monthly_tokens=1000000),
        ]
        session.add_all(plans)
        await session.commit()

        tenants = [
            Tenant(name="Demo Company"),
            Tenant(name="Demo Company 2"),
            Tenant(name="Demo Company 3"),
        ]
        session.add_all(tenants)
        await session.commit()

        subscriptions = [
            Subscriptions(tenant_id=1, plan_id=1, status="active"),
            Subscriptions(tenant_id=2, plan_id=2, status="inactive"),
            Subscriptions(tenant_id=3, plan_id=2, status="active"),
        ]
        session.add_all(subscriptions)
        await session.commit()
        print("Seeded successfully!")

asyncio.run(seed())
