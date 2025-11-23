"""
Stripe integration routes for subscription management
"""
from fastapi import APIRouter, HTTPException, Request, Header
from pydantic import BaseModel
from typing import Optional
import stripe
import os
from datetime import datetime

from backend.database import MongoDB
from backend.config import settings

router = APIRouter(prefix="/api/stripe", tags=["stripe"])

# Initialize Stripe
if not settings.stripe_secret_key or settings.stripe_secret_key.strip() == "":
    raise ValueError("STRIPE_SECRET_KEY is required for billing service. Please set it in environment variables.")
stripe.api_key = settings.stripe_secret_key
FRONTEND_URL = settings.frontend_url or "http://localhost:5173"

class CreateCheckoutRequest(BaseModel):
    price_id: str
    client_id: str
    user_email: str
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None

class CreatePortalRequest(BaseModel):
    customer_id: str
    return_url: Optional[str] = None

@router.post("/create-checkout-session")
async def create_checkout_session(request: CreateCheckoutRequest):
    """
    Create a Stripe Checkout session for subscription payment
    """
    try:
        # Validate Stripe API key is set
        if not stripe.api_key or stripe.api_key.strip() == "":
            raise HTTPException(
                status_code=500, 
                detail="Stripe API key is not configured. Please set STRIPE_SECRET_KEY environment variable."
            )
        
        # Check if customer already exists
        customers = stripe.Customer.list(email=request.user_email, limit=1)
        
        if customers.data:
            customer = customers.data[0]
        else:
            # Create new customer
            customer = stripe.Customer.create(
                email=request.user_email,
                metadata={
                    "client_id": request.client_id
                }
            )
        
        # Create checkout session
        success_url = request.success_url or f"{FRONTEND_URL}/billing?success=true"
        cancel_url = request.cancel_url or f"{FRONTEND_URL}/pricing?canceled=true"
        
        session = stripe.checkout.Session.create(
            customer=customer.id,
            payment_method_types=["card"],
            line_items=[{
                "price": request.price_id,
                "quantity": 1,
            }],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "client_id": request.client_id
            }
        )
        
        if not session or not session.url:
            raise HTTPException(
                status_code=500,
                detail="Failed to create checkout session: Stripe returned invalid response"
            )
        
        return {
            "sessionId": session.id,
            "url": session.url
        }
    
    except HTTPException:
        raise
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create checkout session: {str(e)}")


@router.post("/create-portal-session")
async def create_portal_session(request: CreatePortalRequest):
    """
    Create a Stripe Customer Portal session for managing subscriptions
    """
    try:
        return_url = request.return_url or f"{FRONTEND_URL}/billing"
        
        session = stripe.billing_portal.Session.create(
            customer=request.customer_id,
            return_url=return_url,
        )
        
        return {
            "url": session.url
        }
    
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create portal session: {str(e)}")


@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    """
    Handle Stripe webhook events
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    webhook_secret = settings.stripe_webhook_secret
    
    if not webhook_secret:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Handle the event
    try:
        if event["type"] == "checkout.session.completed":
            await handle_checkout_completed(event["data"]["object"])
        
        elif event["type"] == "customer.subscription.updated":
            await handle_subscription_updated(event["data"]["object"])
        
        elif event["type"] == "customer.subscription.deleted":
            await handle_subscription_deleted(event["data"]["object"])
        
        elif event["type"] == "invoice.paid":
            await handle_invoice_paid(event["data"]["object"])
        
        elif event["type"] == "invoice.payment_failed":
            await handle_invoice_payment_failed(event["data"]["object"])
        
        return {"status": "success"}
    
    except Exception as e:
        print(f"Webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Webhook handler failed: {str(e)}")


async def handle_checkout_completed(session):
    """Handle successful checkout"""
    client_id = session["metadata"]["client_id"]
    customer_id = session["customer"]
    subscription_id = session["subscription"]
    
    # Get subscription details from Stripe
    subscription = stripe.Subscription.retrieve(subscription_id)
    
    # Determine tier from price ID
    price_id = subscription["items"]["data"][0]["price"]["id"]
    tier = "free"  # default
    
    # Note: These env vars are frontend vars, we need to determine tier differently
    # For now, hardcode the price IDs (TODO: store in database)
    if price_id == "price_1SVgiJIg5hGtAstv8SImfqS8":
        tier = "manager"
    elif price_id == "price_1SVghCIg5hGtAstvggGBn0eO":
        tier = "expert"
    
    # Store subscription in MongoDB
    subscriptions_collection = MongoDB.client["c_monitor_shared"]["subscriptions"]
    
    subscription_doc = {
        "client_id": client_id,
        "stripe_customer_id": customer_id,
        "stripe_subscription_id": subscription_id,
        "tier": tier,
        "status": subscription["status"],
        "current_period_start": datetime.fromtimestamp(subscription["current_period_start"]).isoformat(),
        "current_period_end": datetime.fromtimestamp(subscription["current_period_end"]).isoformat(),
        "cancel_at_period_end": subscription["cancel_at_period_end"],
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    
    # Upsert subscription
    await subscriptions_collection.update_one(
        {"stripe_subscription_id": subscription_id},
        {"$set": subscription_doc},
        upsert=True
    )
    
    print(f"Subscription created for client {client_id}: {tier}")


async def handle_subscription_updated(subscription):
    """Handle subscription updates"""
    subscription_id = subscription["id"]
    
    subscriptions_collection = MongoDB.client["c_monitor_shared"]["subscriptions"]
    
    update_doc = {
        "status": subscription["status"],
        "current_period_start": datetime.fromtimestamp(subscription["current_period_start"]).isoformat(),
        "current_period_end": datetime.fromtimestamp(subscription["current_period_end"]).isoformat(),
        "cancel_at_period_end": subscription["cancel_at_period_end"],
        "updated_at": datetime.utcnow().isoformat()
    }
    
    await subscriptions_collection.update_one(
        {"stripe_subscription_id": subscription_id},
        {"$set": update_doc}
    )
    
    print(f"Subscription updated: {subscription_id}")


async def handle_subscription_deleted(subscription):
    """Handle subscription cancellation"""
    subscription_id = subscription["id"]
    
    subscriptions_collection = MongoDB.client["c_monitor_shared"]["subscriptions"]
    
    await subscriptions_collection.update_one(
        {"stripe_subscription_id": subscription_id},
        {"$set": {
            "status": "canceled",
            "updated_at": datetime.utcnow().isoformat()
        }}
    )
    
    print(f"Subscription canceled: {subscription_id}")


async def handle_invoice_paid(invoice):
    """Handle successful invoice payment"""
    subscription_id = invoice.get("subscription")
    if not subscription_id:
        return
    
    invoices_collection = MongoDB.client["c_monitor_shared"]["invoices"]
    
    # Get client_id from subscription
    subscriptions_collection = MongoDB.client["c_monitor_shared"]["subscriptions"]
    subscription_doc = await subscriptions_collection.find_one({"stripe_subscription_id": subscription_id})
    
    if not subscription_doc:
        return
    
    invoice_doc = {
        "client_id": subscription_doc["client_id"],
        "stripe_invoice_id": invoice["id"],
        "stripe_subscription_id": subscription_id,
        "amount": invoice["amount_paid"] / 100,  # Convert from cents
        "currency": invoice["currency"].upper(),
        "status": "paid",
        "invoice_url": invoice.get("hosted_invoice_url"),
        "paid_at": datetime.fromtimestamp(invoice["status_transitions"]["paid_at"]).isoformat() if invoice["status_transitions"]["paid_at"] else None,
        "created_at": datetime.fromtimestamp(invoice["created"]).isoformat()
    }
    
    await invoices_collection.update_one(
        {"stripe_invoice_id": invoice["id"]},
        {"$set": invoice_doc},
        upsert=True
    )
    
    print(f"Invoice paid: {invoice['id']}")


async def handle_invoice_payment_failed(invoice):
    """Handle failed invoice payment"""
    subscription_id = invoice.get("subscription")
    if not subscription_id:
        return
    
    # Update subscription status
    subscriptions_collection = MongoDB.client["c_monitor_shared"]["subscriptions"]
    
    await subscriptions_collection.update_one(
        {"stripe_subscription_id": subscription_id},
        {"$set": {
            "status": "past_due",
            "updated_at": datetime.utcnow().isoformat()
        }}
    )
    
    print(f"Invoice payment failed: {invoice['id']}")


@router.get("/billing/{client_id}")
async def get_billing_info(client_id: str):
    """
    Get subscription and invoice information for a client
    """
    try:
        subscriptions_collection = MongoDB.client["c_monitor_shared"]["subscriptions"]
        invoices_collection = MongoDB.client["c_monitor_shared"]["invoices"]
        
        # Get subscription
        subscription = await subscriptions_collection.find_one({"client_id": client_id})
        
        if not subscription:
            return {
                "subscription": None,
                "invoices": [],
                "usage": {
                    "productsCreated": 0,
                    "productsLimit": 5,  # Free tier default
                    "dataRetentionDays": 7,
                    "currentPeriodStart": datetime.utcnow().isoformat(),
                    "currentPeriodEnd": datetime.utcnow().isoformat()
                }
            }
        
        # Get invoices
        invoices_cursor = invoices_collection.find({"client_id": client_id}).sort("created_at", -1).limit(10)
        invoices = await invoices_cursor.to_list(length=10)
        
        # Get usage stats
        products_collection = MongoDB.client[f"c_monitor_{client_id}"]["products"]
        
        # Count products created in current period
        current_period_start = datetime.fromisoformat(subscription["current_period_start"])
        products_count = await products_collection.count_documents({
            "createdAt": {"$gte": current_period_start.isoformat()}
        })
        
        # Get plan limits
        tier = subscription["tier"]
        limits = {
            "free": {"productsPerMonth": 5, "dataRetentionDays": 7},
            "manager": {"productsPerMonth": 50, "dataRetentionDays": 90},
            "expert": {"productsPerMonth": None, "dataRetentionDays": None},
            "enterprise": {"productsPerMonth": None, "dataRetentionDays": None}
        }
        
        plan_limits = limits.get(tier, limits["free"])
        
        # Remove MongoDB _id from documents
        if subscription:
            subscription.pop("_id", None)
        for invoice in invoices:
            invoice.pop("_id", None)
        
        return {
            "subscription": subscription,
            "invoices": invoices,
            "usage": {
                "productsCreated": products_count,
                "productsLimit": plan_limits["productsPerMonth"],
                "dataRetentionDays": plan_limits["dataRetentionDays"],
                "currentPeriodStart": subscription["current_period_start"],
                "currentPeriodEnd": subscription["current_period_end"]
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get billing info: {str(e)}")

