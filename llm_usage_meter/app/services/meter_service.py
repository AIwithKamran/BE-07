from sqlalchemy import select, func, extract
from datetime import datetime
from models.usage_event import UsageEvent
from models.subscriptions import Subscriptions
from models.plan import Plan

async def record_usage(session, tenant_id, event_type, quantity, idempotency_key):
    # 1) Idempotency check — prevents double-counting
    existing = await session.execute(
        select(UsageEvent).where(UsageEvent.idempotency_key == idempotency_key)
    )
    existing_event = existing.scalar_one_or_none()
    if existing_event:
        return existing_event, True  # True = duplicate, no new event created

    # 2) Fetch active subscription
    sub_result = await session.execute(
        select(Subscriptions).where(
            Subscriptions.tenant_id == tenant_id,
            Subscriptions.status == "active"
        )
    )
    subscription = sub_result.scalar_one_or_none()
    if not subscription:
        raise ValueError(f"No active subscription for tenant {tenant_id}")

    # 3) Fetch the plan (separate query, no relationship needed)
    plan_result = await session.execute(
        select(Plan).where(Plan.id == subscription.plan_id)
    )
    plan = plan_result.scalar_one()

    # 4) Get current month's usage by SUMMING usage events
    now = datetime.utcnow()
    usage_result = await session.execute(
        select(func.coalesce(func.sum(UsageEvent.quantity), 0))
        .where(
            UsageEvent.tenant_id == tenant_id,
            UsageEvent.event_type == event_type,
            extract('month', UsageEvent.created_at) == now.month,
            extract('year', UsageEvent.created_at) == now.year,
        )
    )
    current_usage = usage_result.scalar()

    # 5) Check limit against plan
    if event_type == "api_call":
        limit = plan.api_calls
    elif event_type == "ai_tokens":
        limit = plan.monthly_tokens
    else:
        raise ValueError(f"Unknown event type: {event_type}")

    if current_usage + quantity > limit:
        raise ValueError("Usage limit exceeded")

    # 6) Create usage event
    event = UsageEvent(
        tenant_id=tenant_id,
        event_type=event_type,
        quantity=quantity,
        idempotency_key=idempotency_key,
    )
    session.add(event)
    await session.commit()

    return event, False  # False = new event, not a duplicate
