from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.database import get_db
from models.subscriptions import Subscriptions
from models.plan import Plan
import os
import json
import requests
import hmac
import hashlib
from dotenv import load_dotenv

load_dotenv()

SAFEPAY_API_KEY = os.getenv("SAFEPAY_KEY")
# Safepay test mode URL for creating a tracker/order
# You might need to update this URL based on Safepay API docs
checkout_url = "https://sandbox.api.getsafepay.com/order/v1/init"

router = APIRouter()

class CheckoutRequest(BaseModel):
    tenant_id: int

@router.post("/checkout")
async def create_checkout(request: CheckoutRequest, session: AsyncSession = Depends(get_db)):
    # 1. Fetch active subscription
    sub_result = await session.execute(
        select(Subscriptions).where(
            Subscriptions.tenant_id == request.tenant_id,
            Subscriptions.status == "active"
        )
    )
    subscription = sub_result.scalar_one_or_none()

    if not subscription:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "no_active_subscription",
                "message": "No active subscription found"
            }
        )
    
    # 2. Fetch the plan details
    plan_result = await session.execute(
        select(Plan).where(Plan.id == subscription.plan_id)
    )
    plan = plan_result.scalar_one_or_none()
    
    # 3. Check if they are already on the Pro plan
    if plan.name == 'pro':
        raise HTTPException(status_code=400, detail="Tenant is already on the Pro Plan.")

    # 4. We are on the Free plan, let's create a Safepay Checkout!
    
    # Pro plan costs (this should ideally be pulled from config.py)
    # Safepay expects amount in paisas/cents (e.g., 1000 = 10.00 Rs)
    pro_plan_price = 500000 
    
    payload = json.dumps({
        "client": SAFEPAY_API_KEY,
        "amount": pro_plan_price,
        "currency": "PKR",
        "environment": "sandbox"
    })
    
    headers = {
        'Content-Type': 'application/json'   
    }

    # Make the HTTP request to Safepay
    response = requests.request("POST", checkout_url, headers=headers, data=payload)
    
    if response.status_code == 200:
        # Safepay returns a token/tracker that you use to redirect the user
        response_data = response.json()
        
        # NOTE: You will need to extract the token from response_data 
        # and construct the redirect URL based on Safepay docs!
        return {
            "status": "success",
            "message": "Checkout session created",
            "data": response_data
        }
    else:
        # If Safepay request failed
        raise HTTPException(
            status_code=400, 
            detail=f"Safepay error: {response.text}"
        )

@router.post("/webhooks/safepay")
async def safepay_webhook(request: Request, session: AsyncSession = Depends(get_db)):
    # 1. Get the raw body and the signature header
    payload = await request.body()
    signature = request.headers.get("x-sfpy-signature") # Note: Check Safepay docs for the exact header name!
    if not signature:
        raise HTTPException(status_code=400, detail="Missing signature")
    # 2. Verify the Webhook Signature (To prove it's actually Safepay and not a hacker!)
    # This fulfills PROBE 4 of the Capstone
    safepay_secret = os.getenv("SAFEPAY_WEBHOOK_SECRET")
    expected_sig = hmac.new(
        safepay_secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(expected_sig, signature):
        raise HTTPException(status_code=400, detail="Invalid webhook signature")
    # 3. Parse the JSON payload
    data = await request.json()
    
    # Check if the payment was successful
    # Note: Safepay might use a different event name like "payment.success"
    if data.get("event") == "payment.success":
        # Extract the tenant_id from the Safepay metadata
        # (You would need to pass this tenant_id when you created the checkout!)
        tenant_id = data["metadata"]["tenant_id"] 
        
        # 4. Fetch the tenant's subscription from the database
        sub_result = await session.execute(
            select(Subscriptions).where(Subscriptions.tenant_id == int(tenant_id))
        )
        subscription = sub_result.scalar_one_or_none()
        if subscription:
            # 5. Upgrade them to the Pro plan! (Assuming Pro plan ID is 2)
            subscription.plan_id = 2 
            await session.commit()
            return {"status": "success", "message": "Upgraded to Pro!"}
    return {"status": "ignored"}