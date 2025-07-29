# Secure PayPal Integration for Viral Daily

from fastapi import APIRouter, HTTPException, Request, Depends
from typing import Optional
import os
from datetime import datetime
import logging
import json

from models import PaymentTransaction, PaymentStatus, SubscriptionTier, User, CheckoutRequest
from subscription_plans import get_plan
from auth import get_current_user, require_user

# PayPal SDK imports
from paypalcheckoutsdk.core import SandboxEnvironment, LiveEnvironment, PayPalHttpClient
from paypalcheckoutsdk.orders import OrdersCreateRequest, OrdersCaptureRequest, OrdersGetRequest
from paypalcheckoutsdk.payments import CapturesRefundRequest

logger = logging.getLogger(__name__)

class PayPalService:
    def __init__(self, db):
        self.db = db
        self.client_id = os.environ.get('PAYPAL_CLIENT_ID')
        self.client_secret = os.environ.get('PAYPAL_CLIENT_SECRET')
        self.mode = os.environ.get('PAYPAL_MODE', 'sandbox')
        
        if not self.client_id or not self.client_secret:
            logger.warning("PayPal credentials not configured. PayPal payments will not be available.")
            self.client = None
        else:
            # Initialize PayPal environment
            if self.mode == 'live':
                environment = LiveEnvironment(client_id=self.client_id, client_secret=self.client_secret)
            else:
                environment = SandboxEnvironment(client_id=self.client_id, client_secret=self.client_secret)
            
            self.client = PayPalHttpClient(environment)
            logger.info(f"PayPal client initialized in {self.mode} mode")
    
    def is_available(self) -> bool:
        """Check if PayPal is properly configured"""
        return self.client is not None
    
    async def create_subscription_order(self, subscription_tier: SubscriptionTier, 
                                      billing_cycle: str, user: Optional[User] = None,
                                      host_url: str = "") -> dict:
        """Create a PayPal order for subscription payment"""
        if not self.is_available():
            raise HTTPException(status_code=503, detail="PayPal payments are not available")
        
        try:
            # Get plan details
            plan = get_plan(subscription_tier)
            if not plan or plan.tier == SubscriptionTier.FREE:
                raise HTTPException(status_code=400, detail="Invalid subscription tier for payment")
            
            # Calculate amount
            amount = plan.price_yearly if billing_cycle == "yearly" else plan.price_monthly
            
            # Create order request
            request = OrdersCreateRequest()
            request.prefer('return=representation')
            
            # Order details
            order_data = {
                "intent": "CAPTURE",
                "application_context": {
                    "brand_name": "Viral Daily",
                    "landing_page": "BILLING",
                    "user_action": "PAY_NOW",
                    "return_url": f"{host_url}/subscription/paypal/success",
                    "cancel_url": f"{host_url}/subscription/paypal/cancel"
                },
                "purchase_units": [{
                    "reference_id": f"viral_daily_{subscription_tier.value}_{billing_cycle}",
                    "description": f"Viral Daily {plan.name} Plan - {billing_cycle.capitalize()} Billing",
                    "amount": {
                        "currency_code": "EUR",
                        "value": f"{amount:.2f}",
                        "breakdown": {
                            "item_total": {
                                "currency_code": "EUR",
                                "value": f"{amount:.2f}"
                            }
                        }
                    },
                    "items": [{
                        "name": f"Viral Daily {plan.name} Plan",
                        "description": f"{billing_cycle.capitalize()} subscription to Viral Daily {plan.name}",
                        "unit_amount": {
                            "currency_code": "EUR",
                            "value": f"{amount:.2f}"
                        },
                        "quantity": "1",
                        "category": "DIGITAL_GOODS"
                    }]
                }]
            }
            
            request.request_body(order_data)
            
            # Execute request
            response = self.client.execute(request)
            order = response.result.__dict__
            
            # Store payment transaction
            transaction = PaymentTransaction(
                user_id=user.id if user else None,
                email=user.email if user else None,
                session_id=order['id'],
                payment_id=order['id'],
                amount=amount,
                currency="usd",
                status=PaymentStatus.PENDING,
                payment_method="paypal",
                subscription_tier=subscription_tier,
                metadata={
                    "billing_cycle": billing_cycle,
                    "paypal_order_id": order['id'],
                    "plan_name": plan.name
                }
            )
            
            await self.db.payment_transactions.insert_one(transaction.dict())
            logger.info(f"Created PayPal order {order['id']} for user {user.id if user else 'anonymous'}")
            
            return {
                "order_id": order['id'],
                "approval_url": next((link['href'] for link in order.get('links', []) 
                                    if link['rel'] == 'approve'), None),
                "order_status": order['status']
            }
            
        except Exception as e:
            logger.error(f"Error creating PayPal order: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error creating PayPal payment: {str(e)}")
    
    async def capture_order(self, order_id: str) -> dict:
        """Capture a PayPal order after user approval"""
        if not self.is_available():
            raise HTTPException(status_code=503, detail="PayPal payments are not available")
        
        try:
            # Get order details first
            get_request = OrdersGetRequest(order_id)
            get_response = self.client.execute(get_request)
            order_details = get_response.result.__dict__
            
            # Capture the order
            capture_request = OrdersCaptureRequest(order_id)
            capture_response = self.client.execute(capture_request)
            capture_result = capture_response.result.__dict__
            
            # Update payment transaction
            await self.db.payment_transactions.update_one(
                {"session_id": order_id},
                {
                    "$set": {
                        "status": PaymentStatus.COMPLETED.value,
                        "completed_at": datetime.utcnow(),
                        "payment_id": capture_result['id']
                    }
                }
            )
            
            # Get transaction to update user subscription
            transaction = await self.db.payment_transactions.find_one({"session_id": order_id})
            if transaction:
                await self._process_successful_payment(transaction)
            
            logger.info(f"Successfully captured PayPal order {order_id}")
            
            return {
                "capture_id": capture_result['id'],
                "status": capture_result['status'],
                "amount": capture_result.get('purchase_units', [{}])[0].get('amount', {}).get('value'),
                "currency": capture_result.get('purchase_units', [{}])[0].get('amount', {}).get('currency_code')
            }
            
        except Exception as e:
            logger.error(f"Error capturing PayPal order {order_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error processing PayPal payment: {str(e)}")
    
    async def _process_successful_payment(self, transaction: dict):
        """Process successful PayPal payment and update user subscription"""
        try:
            from auth import auth_service
            
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
                user = await auth_service.create_user(email)
            
            if user:
                await auth_service.update_user_subscription(
                    user.id,
                    subscription_tier,
                    stripe_customer_id=None,  # PayPal doesn't use customer IDs
                    stripe_subscription_id=transaction.get("session_id")
                )
                logger.info(f"Updated user {user.id} to {subscription_tier.value} subscription via PayPal")
            
        except Exception as e:
            logger.error(f"Error processing PayPal payment: {str(e)}")
    
    async def handle_webhook(self, request_body: bytes, headers: dict) -> dict:
        """Handle PayPal webhook events"""
        try:
            webhook_data = json.loads(request_body.decode('utf-8'))
            event_type = webhook_data.get('event_type')
            
            logger.info(f"Received PayPal webhook: {event_type}")
            
            # Handle different webhook events
            if event_type == "CHECKOUT.ORDER.APPROVED":
                # Order was approved by user
                order_id = webhook_data.get('resource', {}).get('id')
                if order_id:
                    # Optionally auto-capture here or wait for manual capture
                    pass
                    
            elif event_type == "PAYMENT.CAPTURE.COMPLETED":
                # Payment was successfully captured
                capture_id = webhook_data.get('resource', {}).get('id')
                order_id = webhook_data.get('resource', {}).get('supplementary_data', {}).get('related_ids', {}).get('order_id')
                
                if order_id:
                    # Update transaction status
                    await self.db.payment_transactions.update_one(
                        {"session_id": order_id},
                        {
                            "$set": {
                                "status": PaymentStatus.COMPLETED.value,
                                "completed_at": datetime.utcnow()
                            }
                        }
                    )
            
            return {"status": "success", "event_type": event_type}
            
        except Exception as e:
            logger.error(f"Error handling PayPal webhook: {str(e)}")
            raise HTTPException(status_code=400, detail="Webhook processing failed")
    
    async def get_payment_status(self, order_id: str) -> dict:
        """Get the status of a PayPal order"""
        if not self.is_available():
            raise HTTPException(status_code=503, detail="PayPal payments are not available")
        
        try:
            request = OrdersGetRequest(order_id)
            response = self.client.execute(request)
            order = response.result.__dict__
            
            return {
                "order_id": order['id'],
                "status": order['status'],
                "intent": order['intent'],
                "purchase_units": order.get('purchase_units', [])
            }
            
        except Exception as e:
            logger.error(f"Error getting PayPal order status: {str(e)}")
            raise HTTPException(status_code=500, detail="Error checking payment status")


def create_paypal_router(db) -> APIRouter:
    """Create PayPal payment router with all PayPal endpoints"""
    router = APIRouter(prefix="/api/payments/paypal")
    paypal_service = PayPalService(db)
    
    @router.get("/available")
    async def check_paypal_availability():
        """Check if PayPal payments are available"""
        return {
            "available": paypal_service.is_available(),
            "mode": os.environ.get('PAYPAL_MODE', 'sandbox')
        }
    
    @router.post("/create-order")
    async def create_paypal_order(
        request_data: CheckoutRequest,
        request: Request,
        user: Optional[User] = Depends(get_current_user)
    ):
        """Create a PayPal order for subscription payment"""
        host_url = str(request.base_url).rstrip('/')
        return await paypal_service.create_subscription_order(
            request_data.subscription_tier,
            request_data.billing_cycle,
            user,
            host_url
        )
    
    @router.post("/capture-order/{order_id}")
    async def capture_paypal_order(order_id: str):
        """Capture a PayPal order after user approval"""
        return await paypal_service.capture_order(order_id)
    
    @router.get("/order-status/{order_id}")
    async def get_order_status(order_id: str):
        """Get PayPal order status"""
        return await paypal_service.get_payment_status(order_id)
    
    @router.post("/webhook")
    async def paypal_webhook(request: Request):
        """Handle PayPal webhooks"""
        body = await request.body()
        headers = dict(request.headers)
        return await paypal_service.handle_webhook(body, headers)
    
    @router.get("/config")
    async def get_paypal_config():
        """Get PayPal configuration for frontend"""
        return {
            "client_id": os.environ.get('PAYPAL_CLIENT_ID'),
            "mode": os.environ.get('PAYPAL_MODE', 'sandbox'),
            "currency": "EUR"
        }
    
    return router