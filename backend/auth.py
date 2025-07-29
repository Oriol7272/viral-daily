# Authentication and Authorization System

from fastapi import HTTPException, Depends, Header
from typing import Optional
import secrets
import hashlib
from motor.motor_asyncio import AsyncIOMotorDatabase
from models import User, SubscriptionTier, APIUsage
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    def generate_api_key(self) -> str:
        """Generate a secure API key"""
        random_bytes = secrets.token_bytes(32)
        api_key = hashlib.sha256(random_bytes).hexdigest()
        return f"vd_{api_key[:32]}"  # vd = Viral Daily
    
    async def create_user(self, email: str, name: Optional[str] = None) -> User:
        """Create a new user with API key"""
        # Check if user exists
        existing_user = await self.db.users.find_one({"email": email})
        if existing_user:
            return User(**existing_user)
        
        # Create new user
        user = User(
            email=email,
            name=name,
            api_key=self.generate_api_key(),
            subscription_tier=SubscriptionTier.FREE
        )
        
        await self.db.users.insert_one(user.dict())
        return user
    
    async def get_user_by_api_key(self, api_key: str) -> Optional[User]:
        """Get user by API key"""
        user_data = await self.db.users.find_one({"api_key": api_key, "is_active": True})
        if user_data:
            return User(**user_data)
        return None
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        user_data = await self.db.users.find_one({"email": email, "is_active": True})
        if user_data:
            return User(**user_data)
        return None
    
    async def update_user_subscription(self, user_id: str, tier: SubscriptionTier, 
                                     stripe_customer_id: str = None, 
                                     stripe_subscription_id: str = None) -> bool:
        """Update user subscription tier"""
        update_data = {
            "subscription_tier": tier.value,
            "subscription_expires_at": datetime.utcnow() + timedelta(days=30)
        }
        
        if stripe_customer_id:
            update_data["stripe_customer_id"] = stripe_customer_id
        if stripe_subscription_id:
            update_data["stripe_subscription_id"] = stripe_subscription_id
        
        # Update API limits based on tier
        if tier == SubscriptionTier.PRO:
            update_data["max_daily_api_calls"] = 10000
        elif tier == SubscriptionTier.BUSINESS:
            update_data["max_daily_api_calls"] = 100000
        
        result = await self.db.users.update_one(
            {"id": user_id},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    async def check_api_rate_limit(self, user: User) -> bool:
        """Check if user has exceeded API rate limit"""
        # Reset daily counter if it's a new day
        today = datetime.utcnow().date()
        user_day_start = datetime.combine(today, datetime.min.time())
        
        # Count API calls today
        calls_today = await self.db.api_usage.count_documents({
            "$or": [
                {"user_id": user.id},
                {"api_key": user.api_key}
            ],
            "timestamp": {"$gte": user_day_start}
        })
        
        return calls_today < user.max_daily_api_calls
    
    async def log_api_usage(self, user: Optional[User], endpoint: str, method: str, 
                          api_key: Optional[str] = None, response_time_ms: float = None,
                          status_code: int = 200, error_message: str = None):
        """Log API usage for analytics"""
        usage = APIUsage(
            user_id=user.id if user else None,
            api_key=api_key,
            endpoint=endpoint,
            method=method,
            response_time_ms=response_time_ms,
            status_code=status_code,
            error_message=error_message
        )
        
        await self.db.api_usage.insert_one(usage.dict())
    
    async def get_user_analytics(self, user_id: str, days: int = 30) -> dict:
        """Get user analytics data"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        pipeline = [
            {
                "$match": {
                    "user_id": user_id,
                    "timestamp": {"$gte": start_date}
                }
            },
            {
                "$group": {
                    "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}},
                    "api_calls": {"$sum": 1},
                    "avg_response_time": {"$avg": "$response_time_ms"}
                }
            },
            {"$sort": {"_id": 1}}
        ]
        
        usage_by_day = await self.db.api_usage.aggregate(pipeline).to_list(days)
        total_calls = await self.db.api_usage.count_documents({
            "user_id": user_id,
            "timestamp": {"$gte": start_date}
        })
        
        return {
            "total_api_calls": total_calls,
            "usage_by_day": {item["_id"]: item["api_calls"] for item in usage_by_day},
            "avg_response_time": sum(item["avg_response_time"] or 0 for item in usage_by_day) / len(usage_by_day) if usage_by_day else 0
        }

# Dependency functions for FastAPI
async def get_current_user(
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None),
    db = None
) -> Optional[User]:
    """Get current user from API key (optional)"""
    api_key = None
    
    # Check Authorization header (Bearer token)
    if authorization and authorization.startswith("Bearer "):
        api_key = authorization.split(" ")[1]
    
    # Check X-API-Key header
    elif x_api_key:
        api_key = x_api_key
    
    if not api_key:
        return None
    
    auth_service = AuthService(db)
    return await auth_service.get_user_by_api_key(api_key)

async def require_user(
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None),
    db = None
) -> User:
    """Require authenticated user"""
    user = await get_current_user(authorization, x_api_key, db)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key or authentication required"
        )
    return user

async def require_pro_user(user: User = Depends(require_user)) -> User:
    """Require Pro or Business tier user"""
    if user.subscription_tier == SubscriptionTier.FREE:
        raise HTTPException(
            status_code=403,
            detail="Pro or Business subscription required for this feature"
        )
    return user

async def require_business_user(user: User = Depends(require_user)) -> User:
    """Require Business tier user"""
    if user.subscription_tier != SubscriptionTier.BUSINESS:
        raise HTTPException(
            status_code=403,
            detail="Business subscription required for this feature"
        )
    return user

async def check_rate_limit(user: Optional[User], db) -> bool:
    """Check API rate limits"""
    if not user:
        return True  # Allow anonymous access with basic limits
    
    auth_service = AuthService(db)
    return await auth_service.check_api_rate_limit(user)