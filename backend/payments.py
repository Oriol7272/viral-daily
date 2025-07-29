# Payment System with Stripe Integration

from fastapi import APIRouter, HTTPException, Request, Header, Depends
from typing import Optional
import os
from datetime import datetime
import logging

from models import CheckoutRequest, PaymentTransaction, PaymentStatus, SubscriptionTier, User
from subscription_plans import get_stripe_price_id, get_plan
from auth import AuthService, get_current_user, require_user
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest

logger = logging.getLogger(__name__)

class PaymentService:
    def __init__(self, db, auth_service: AuthService):
        self.db = db
        self.auth_service = auth_service
        self.stripe_api_key = os.environ.get('STRIPE_API_KEY')
        self.stripe_checkout = None
        
    def get_stripe_checkout(self, host_url: str):
        """Initialize Stripe checkout with webhook URL"""
        if not self.stripe_checkout:
            webhook_url = f"{host_url}/api/webhook/stripe"
            self.stripe_checkout = StripeCheckout(
                api_key=self.stripe_api_key,
                webhook_url=webhook_url
            )
        return self.stripe_checkout
    
    async def create_checkout_session(self, request_data: CheckoutRequest, 
                                    host_url: str, user: Optional[User] = None) -> CheckoutSessionResponse:
        """Create a Stripe checkout session for subscription"""
        try:
            # Get plan details
            plan = get_plan(request_data.subscription_tier)
            if not plan:
                raise HTTPException(status_code=400, detail="Invalid subscription tier")
            
            # Get Stripe price ID
            stripe_price_id = get_stripe_price_id(request_data.subscription_tier, request_data.billing_cycle)
            if not stripe_price_id:
                raise HTTPException(status_code=400, detail="Subscription tier not available for purchase")
            
            # Calculate amount
            amount = plan.price_yearly if request_data.billing_cycle == "yearly" else plan.price_monthly
            
            # Build URLs
            success_url = f"{host_url}/subscription/success?session_id={{CHECKOUT_SESSION_ID}}"
            cancel_url = f"{host_url}/subscription/cancel"
            
            # Prepare metadata
            metadata = {
                "subscription_tier": request_data.subscription_tier.value,
                "billing_cycle": request_data.billing_cycle,
                "user_id": user.id if user else "",
                "email": request_data.email or (user.email if user else "")
            }
            
            # Create checkout session
            stripe_checkout = self.get_stripe_checkout(host_url)
            checkout_request = CheckoutSessionRequest(
                stripe_price_id=stripe_price_id,
                quantity=1,
                success_url=success_url,
                cancel_url=cancel_url,
                metadata=metadata
            )
            
            session = await stripe_checkout.create_checkout_session(checkout_request)
            
            # Create payment transaction record
            transaction = PaymentTransaction(
                user_id=user.id if user else None,
                email=request_data.email or (user.email if user else None),
                session_id=session.session_id,
                amount=amount,
                currency="usd",
                status=PaymentStatus.PENDING,
                payment_method="stripe",
                stripe_price_id=stripe_price_id,
                subscription_tier=request_data.subscription_tier,
                metadata=metadata
            )
            
            await self.db.payment_transactions.insert_one(transaction.dict())
            logger.info(f"Created payment transaction for session {session.session_id}")
            
            return session
            
        except Exception as e:
            logger.error(f"Error creating checkout session: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error creating checkout session: {str(e)}")
    
    async def get_checkout_status(self, session_id: str) -> CheckoutStatusResponse:
        """Get the status of a checkout session"""
        try:
            # Get transaction from database
            transaction = await self.db.payment_transactions.find_one({"session_id": session_id})
            if not transaction:
                raise HTTPException(status_code=404, detail="Payment session not found")
            
            # If already processed successfully, return cached status
            if transaction.get("status") == PaymentStatus.COMPLETED.value:
                return CheckoutStatusResponse(
                    status="complete",
                    payment_status="paid",
                    amount_total=int(transaction["amount"] * 100),  # Convert to cents
                    currency=transaction["currency"],
                    metadata=transaction.get("metadata", {})
                )
            
            # Get status from Stripe
            stripe_checkout = self.get_stripe_checkout("https://example.com")  # Host doesn't matter for status check
            checkout_status = await stripe_checkout.get_checkout_status(session_id)
            
            # Update transaction status if payment completed
            if checkout_status.payment_status == "paid" and transaction.get("status") != PaymentStatus.COMPLETED.value:
                await self._process_successful_payment(session_id, transaction)
            
            return checkout_status
            
        except Exception as e:
            logger.error(f"Error getting checkout status: {str(e)}")
            raise HTTPException(status_code=500, detail="Error checking payment status")
    
    async def _process_successful_payment(self, session_id: str, transaction: dict):
        """Process a successful payment"""
        try:
            # Update transaction status
            await self.db.payment_transactions.update_one(
                {"session_id": session_id},
                {
                    "$set": {
                        "status": PaymentStatus.COMPLETED.value,
                        "completed_at": datetime.utcnow()
                    }
                }
            )
            
            # Update user subscription
            user_id = transaction.get("user_id")
            email = transaction.get("email")
            subscription_tier = SubscriptionTier(transaction.get("subscription_tier"))
            
            user = None
            if user_id:
                user_data = await self.db.users.find_one({"id": user_id})
                if user_data:
                    user = User(**user_data)
            elif email:
                # Create user if doesn't exist
                user = await self.auth_service.create_user(email)
            
            if user:
                await self.auth_service.update_user_subscription(
                    user.id,
                    subscription_tier,
                    stripe_customer_id=transaction.get("customer_id"),
                    stripe_subscription_id=session_id
                )
                logger.info(f"Updated user {user.id} to {subscription_tier.value} subscription")
            
        except Exception as e:
            logger.error(f"Error processing successful payment: {str(e)}")
    
    async def handle_webhook(self, request_body: bytes, stripe_signature: str):
        """Handle Stripe webhook events"""
        try:
            stripe_checkout = self.get_stripe_checkout("https://example.com")
            webhook_response = await stripe_checkout.handle_webhook(request_body, stripe_signature)
            
            # Process webhook based on event type
            if webhook_response.event_type == "checkout.session.completed":
                session_id = webhook_response.session_id
                
                # Get transaction
                transaction = await self.db.payment_transactions.find_one({"session_id": session_id})
                if transaction and transaction.get("status") != PaymentStatus.COMPLETED.value:
                    await self._process_successful_payment(session_id, transaction)
            
            return {"status": "success", "event_type": webhook_response.event_type}
            
        except Exception as e:
            logger.error(f"Error handling webhook: {str(e)}")
            raise HTTPException(status_code=400, detail="Webhook processing failed")


def create_payment_router(db, auth_service: AuthService) -> APIRouter:
    """Create payment router with all payment endpoints"""
    router = APIRouter(prefix="/api/payments/v1")
    payment_service = PaymentService(db, auth_service)
    
    @router.post("/checkout/session", response_model=CheckoutSessionResponse)
    async def create_checkout_session(
        request_data: CheckoutRequest,
        request: Request,
        user: Optional[User] = Depends(get_current_user)
    ):
        """Create a Stripe checkout session"""
        host_url = str(request.base_url).rstrip('/')
        return await payment_service.create_checkout_session(request_data, host_url, user)
    
    @router.get("/checkout/status/{session_id}", response_model=CheckoutStatusResponse)
    async def get_checkout_status(session_id: str):
        """Get checkout session status"""
        return await payment_service.get_checkout_status(session_id)
    
    @router.post("/webhook/stripe")
    async def stripe_webhook(
        request: Request,
        stripe_signature: str = Header(..., alias="Stripe-Signature")
    ):
        """Handle Stripe webhooks"""
        body = await request.body()
        return await payment_service.handle_webhook(body, stripe_signature)
    
    @router.get("/transactions/me")
    async def get_my_transactions(user: User = Depends(require_user)):
        """Get current user's payment transactions"""
        try:
            transactions = await db.payment_transactions.find(
                {"user_id": user.id}
            ).sort("created_at", -1).to_list(50)
            return {"transactions": transactions, "total": len(transactions)}
        except Exception as e:
            logger.error(f"Error fetching user transactions: {str(e)}")
            raise HTTPException(status_code=500, detail="Error fetching transactions")
    
    return router