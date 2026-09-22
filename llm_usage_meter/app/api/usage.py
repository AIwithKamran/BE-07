from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract
from datetime import datetime

from core.database import get_db
from services.meter_service import record_usage
from services.cost_service import calculate_cost
from models.usage_event import UsageEvent
from models.subscriptions import Subscriptions
from models.plan import Plan

router = APIRouter()


# Request body schema — Pydantic validates this automatically
class GenerateRequest(BaseModel):
    tenant_id: int
    event_type: str          # "api_call" or "ai_tokens"
    quantity: int
    idempotency_key: str
    token_type: str = None   # "input", "output", or "thinking" (optional)


# ──────────────────────────────────────────────
# POST /generate — the billable endpoint
# ──────────────────────────────────────────────
@router.post("/generate")
async def generate(request: GenerateRequest, session: AsyncSession = Depends(get_db)):
    try:
        result = await record_usage(
            session=session,
            tenant_id=request.tenant_id,
            event_type=request.event_type,
            quantity=request.quantity,
            idempotency_key=request.idempotency_key,
        )
        event, was_duplicate = result

        # Calculate the cost based on token category pricing
        cost = calculate_cost(
            event_type=event.event_type,
            quantity=event.quantity,
            token_type=request.token_type
        )

        if was_duplicate:
            # Same idempotency key sent again — return original result
            return {
                "status": "duplicate",
                "message": "This request was already processed",
                "event_id": event.id,
                "idempotency_key": event.idempotency_key,
                "calculated_cost_cents": cost
            }

        # New event created successfully
        return {
            "status": "created",
            "message": "Usage recorded successfully",
            "event_id": event.id,
            "event_type": event.event_type,
            "token_type": request.token_type,
            "quantity": event.quantity,
            "idempotency_key": event.idempotency_key,
            "calculated_cost_cents": cost
        }

    except ValueError as e:
        error_message = str(e)

        # Quota exceeded → 429
        if "limit exceeded" in error_message.lower():
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "quota_exceeded",
                    "message": "Usage quota exceeded. You have reached your plan limit.",
                    "event_type": request.event_type,
                }
            )

        # No active subscription → 402
        if "no active subscription" in error_message.lower():
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "payment_required",
                    "message": "No active subscription. Please upgrade or subscribe to a plan.",
                }
            )

        # Unknown error
        raise HTTPException(status_code=400, detail=str(e))


# ──────────────────────────────────────────────
# GET /usage/{tenant_id} — the rollup endpoint
# ──────────────────────────────────────────────
@router.get("/usage/{tenant_id}")
async def get_usage(tenant_id: int, session: AsyncSession = Depends(get_db)):
    # 1) Fetch active subscription
    sub_result = await session.execute(
        select(Subscriptions).where(
            Subscriptions.tenant_id == tenant_id,
            Subscriptions.status == "active"
        )
    )
    subscription = sub_result.scalar_one_or_none()
    if not subscription:
        raise HTTPException(status_code=404, detail="No active subscription found")

    # 2) Fetch the plan
    plan_result = await session.execute(
        select(Plan).where(Plan.id == subscription.plan_id)
    )
    plan = plan_result.scalar_one()

    # 3) Calculate current month's usage (rollup)
    now = datetime.utcnow()

    # API calls used this month
    api_calls_result = await session.execute(
        select(func.coalesce(func.sum(UsageEvent.quantity), 0))
        .where(
            UsageEvent.tenant_id == tenant_id,
            UsageEvent.event_type == "api_call",
            extract('month', UsageEvent.created_at) == now.month,
            extract('year', UsageEvent.created_at) == now.year,
        )
    )
    api_calls_used = api_calls_result.scalar()

    # AI tokens used this month
    ai_tokens_result = await session.execute(
        select(func.coalesce(func.sum(UsageEvent.quantity), 0))
        .where(
            UsageEvent.tenant_id == tenant_id,
            UsageEvent.event_type == "ai_tokens",
            extract('month', UsageEvent.created_at) == now.month,
            extract('year', UsageEvent.created_at) == now.year,
        )
    )
    ai_tokens_used = ai_tokens_result.scalar()

    # 4) Return the rollup
    return {
        "tenant_id": tenant_id,
        "plan": plan.name,
        "period": f"{now.year}-{now.month:02d}",
        "api_calls": {
            "used": api_calls_used,
            "limit": plan.api_calls,
            "remaining": plan.api_calls - api_calls_used,
        },
        "ai_tokens": {
            "used": ai_tokens_used,
            "limit": plan.monthly_tokens,
            "remaining": plan.monthly_tokens - ai_tokens_used,
        },
    }