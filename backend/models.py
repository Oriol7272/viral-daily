# Data Models for Viral Daily Monetization System

from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

# Enums
class Platform(str, Enum):
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    TWITTER = "twitter"
    INSTAGRAM = "instagram"

class DeliveryMethod(str, Enum):
    EMAIL = "email"
    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp"

class SubscriptionTier(str, Enum):
    FREE = "free"
    PRO = "pro"
    BUSINESS = "business"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

# Core Models
class ViralVideo(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    url: str
    thumbnail: str
    platform: Platform
    views: Optional[int] = None
    likes: Optional[int] = None
    shares: Optional[int] = None
    author: Optional[str] = None
    duration: Optional[str] = None
    description: Optional[str] = None
    viral_score: float = 0.0
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    published_at: Optional[datetime] = None
    is_sponsored: bool = False
    sponsor_name: Optional[str] = None

class VideoResponse(BaseModel):
    videos: List[ViralVideo]
    total: int
    platform: Optional[Platform] = None
    date: datetime
    has_ads: bool = False
    user_tier: Optional[SubscriptionTier] = None

# User Management
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    name: Optional[str] = None
    subscription_tier: SubscriptionTier = SubscriptionTier.FREE
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    api_key: Optional[str] = None
    daily_api_calls: int = 0
    max_daily_api_calls: int = 100  # Free tier limit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    subscription_expires_at: Optional[datetime] = None
    is_active: bool = True

class UserCreate(BaseModel):
    email: EmailStr
    name: Optional[str] = None

class UserAuth(BaseModel):
    email: EmailStr
    api_key: Optional[str] = None

# Subscription Management
class SubscriptionPlan(BaseModel):
    tier: SubscriptionTier
    name: str
    price_monthly: float
    price_yearly: float
    stripe_price_id_monthly: str
    stripe_price_id_yearly: str
    max_videos_per_day: int
    api_calls_per_day: int
    features: List[str]
    has_ads: bool

class Subscription(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    plan: SubscriptionTier
    stripe_subscription_id: str
    status: str
    current_period_start: datetime
    current_period_end: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
# Payment Processing
class PaymentTransaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    email: Optional[str] = None
    session_id: str
    payment_id: Optional[str] = None
    amount: float
    currency: str = "usd"
    status: PaymentStatus
    payment_method: str
    stripe_price_id: Optional[str] = None
    subscription_tier: Optional[SubscriptionTier] = None
    metadata: Optional[Dict[str, str]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

class CheckoutRequest(BaseModel):
    subscription_tier: SubscriptionTier
    billing_cycle: str = "monthly"  # monthly or yearly
    email: Optional[str] = None

# API Usage Tracking
class APIUsage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    api_key: Optional[str] = None
    endpoint: str
    method: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    response_time_ms: Optional[float] = None
    status_code: int
    error_message: Optional[str] = None

# Analytics Models
class PlatformAnalytics(BaseModel):
    platform: Platform
    total_videos: int
    avg_viral_score: float
    total_views: int
    total_likes: int
    top_videos: List[ViralVideo]
    trending_topics: List[str]

class UserAnalytics(BaseModel):
    user_id: str
    total_api_calls: int
    videos_accessed: int
    favorite_platforms: List[Platform]
    usage_by_day: Dict[str, int]
    subscription_value: float

class SystemAnalytics(BaseModel):
    total_users: int
    total_api_calls: int
    revenue_this_month: float
    active_subscribers: int
    platform_distribution: Dict[Platform, int]
    daily_active_users: int

# Advertising Models
class Advertisement(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    image_url: str
    click_url: str
    advertiser: str
    target_platforms: List[Platform]
    budget: float
    cost_per_click: float
    is_active: bool = True
    impressions: int = 0
    clicks: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AdImpression(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ad_id: str
    user_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    platform: Optional[Platform] = None

class AdClick(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ad_id: str
    user_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    revenue: float

# Legacy Models (for backward compatibility)
class OldSubscription(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: Optional[EmailStr] = None
    telegram_id: Optional[str] = None
    whatsapp_number: Optional[str] = None
    delivery_methods: List[DeliveryMethod]
    active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_delivery: Optional[datetime] = None

class SubscriptionCreate(BaseModel):
    email: Optional[EmailStr] = None
    telegram_id: Optional[str] = None
    whatsapp_number: Optional[str] = None
    delivery_methods: List[DeliveryMethod]