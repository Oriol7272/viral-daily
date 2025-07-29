# Subscription Plans Configuration

from models import SubscriptionPlan, SubscriptionTier

SUBSCRIPTION_PLANS = {
    SubscriptionTier.FREE: SubscriptionPlan(
        tier=SubscriptionTier.FREE,
        name="Free Explorer",
        price_monthly=0.0,
        price_yearly=0.0,
        stripe_price_id_monthly="",
        stripe_price_id_yearly="",
        max_videos_per_day=10,
        api_calls_per_day=100,
        features=[
            "10 viral videos per day",
            "Basic platform access",
            "Limited API calls (100/day)",
            "Community support",
            "Includes advertisements"
        ],
        has_ads=True
    ),
    
    SubscriptionTier.PRO: SubscriptionPlan(
        tier=SubscriptionTier.PRO,
        name="Pro Creator",
        price_monthly=9.99,
        price_yearly=99.99,
        stripe_price_id_monthly="price_pro_monthly",  # Replace with actual Stripe Price IDs
        stripe_price_id_yearly="price_pro_yearly",
        max_videos_per_day=100,
        api_calls_per_day=10000,
        features=[
            "Unlimited viral videos",
            "All platform access",
            "No advertisements",
            "10,000 API calls per day",
            "Email support",
            "Early access to new features",
            "Video analytics",
            "Custom delivery schedules"
        ],
        has_ads=False
    ),
    
    SubscriptionTier.BUSINESS: SubscriptionPlan(
        tier=SubscriptionTier.BUSINESS,
        name="Business Intelligence",
        price_monthly=29.99,
        price_yearly=299.99,
        stripe_price_id_monthly="price_business_monthly",
        stripe_price_id_yearly="price_business_yearly",
        max_videos_per_day=-1,  # Unlimited
        api_calls_per_day=100000,
        features=[
            "Unlimited everything",
            "Full API access",
            "No advertisements",
            "100,000 API calls per day",
            "Priority support",
            "Advanced analytics dashboard",
            "White-label options",
            "Custom integrations",
            "Trend reports and insights",
            "Real-time notifications",
            "Team collaboration tools"
        ],
        has_ads=False
    )
}

def get_plan(tier: SubscriptionTier) -> SubscriptionPlan:
    """Get subscription plan by tier"""
    return SUBSCRIPTION_PLANS.get(tier, SUBSCRIPTION_PLANS[SubscriptionTier.FREE])

def get_stripe_price_id(tier: SubscriptionTier, billing_cycle: str = "monthly") -> str:
    """Get Stripe price ID for a subscription tier and billing cycle"""
    plan = get_plan(tier)
    if billing_cycle == "yearly":
        return plan.stripe_price_id_yearly
    return plan.stripe_price_id_monthly

def calculate_savings(tier: SubscriptionTier) -> float:
    """Calculate yearly savings percentage"""
    plan = get_plan(tier)
    if plan.price_monthly == 0:
        return 0.0
    
    yearly_monthly_equivalent = plan.price_monthly * 12
    savings_percentage = ((yearly_monthly_equivalent - plan.price_yearly) / yearly_monthly_equivalent) * 100
    return round(savings_percentage, 1)