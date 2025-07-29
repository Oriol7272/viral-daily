# Analytics System

from typing import Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from models import PlatformAnalytics, UserAnalytics, SystemAnalytics, Platform, SubscriptionTier
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class AnalyticsService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    async def get_platform_analytics(self, platform: Optional[Platform] = None, 
                                   days: int = 30) -> Dict:
        """Get analytics for platforms"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Build query
        match_query = {"fetched_at": {"$gte": start_date}}
        if platform:
            match_query["platform"] = platform.value
        
        # Aggregate pipeline
        pipeline = [
            {"$match": match_query},
            {
                "$group": {
                    "_id": "$platform",
                    "total_videos": {"$sum": 1},
                    "avg_viral_score": {"$avg": "$viral_score"},
                    "total_views": {"$sum": "$views"},
                    "total_likes": {"$sum": "$likes"},
                    "max_viral_score": {"$max": "$viral_score"}
                }
            },
            {"$sort": {"total_videos": -1}}
        ]
        
        results = await self.db.viral_videos.aggregate(pipeline).to_list(10)
        
        analytics = {}
        for result in results:
            platform_name = result["_id"]
            analytics[platform_name] = {
                "total_videos": result["total_videos"],
                "avg_viral_score": round(result["avg_viral_score"] or 0, 2),
                "total_views": result["total_views"] or 0,
                "total_likes": result["total_likes"] or 0,
                "max_viral_score": round(result["max_viral_score"] or 0, 2)
            }
        
        return analytics
    
    async def get_trending_topics(self, platform: Optional[Platform] = None, 
                                limit: int = 10) -> List[str]:
        """Extract trending topics from video titles"""
        match_query = {}
        if platform:
            match_query["platform"] = platform.value
        
        # Get recent high-scoring videos
        videos = await self.db.viral_videos.find(
            match_query,
            {"title": 1, "viral_score": 1}
        ).sort("viral_score", -1).limit(50).to_list(50)
        
        # Simple keyword extraction (in production, use NLP)
        trending_words = {}
        for video in videos:
            title = video.get("title", "").lower()
            words = title.split()
            for word in words:
                if len(word) > 3 and word.isalpha():
                    trending_words[word] = trending_words.get(word, 0) + 1
        
        # Return top trending words
        sorted_words = sorted(trending_words.items(), key=lambda x: x[1], reverse=True)
        return [word for word, count in sorted_words[:limit]]
    
    async def get_user_analytics(self, user_id: str, days: int = 30) -> UserAnalytics:
        """Get analytics for a specific user"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # API usage analytics
        api_usage = await self.db.api_usage.find({
            "user_id": user_id,
            "timestamp": {"$gte": start_date}
        }).to_list(10000)
        
        # Process API usage data
        total_api_calls = len(api_usage)
        videos_accessed = len([u for u in api_usage if "/videos" in u.get("endpoint", "")])
        
        # Platform preferences
        platform_counts = {}
        for usage in api_usage:
            endpoint = usage.get("endpoint", "")
            if "platform=" in endpoint:
                platform = endpoint.split("platform=")[1].split("&")[0]
                platform_counts[platform] = platform_counts.get(platform, 0) + 1
        
        favorite_platforms = sorted(platform_counts.keys(), 
                                  key=lambda x: platform_counts[x], 
                                  reverse=True)[:3]
        
        # Usage by day
        usage_by_day = {}
        for usage in api_usage:
            date_str = usage["timestamp"].strftime("%Y-%m-%d")
            usage_by_day[date_str] = usage_by_day.get(date_str, 0) + 1
        
        # Calculate subscription value (estimated)
        user = await self.db.users.find_one({"id": user_id})
        subscription_value = 0.0
        if user:
            if user.get("subscription_tier") == "pro":
                subscription_value = 9.99
            elif user.get("subscription_tier") == "business":
                subscription_value = 29.99
        
        return UserAnalytics(
            user_id=user_id,
            total_api_calls=total_api_calls,
            videos_accessed=videos_accessed,
            favorite_platforms=[Platform(p) for p in favorite_platforms if p in Platform.__members__.values()],
            usage_by_day=usage_by_day,
            subscription_value=subscription_value
        )
    
    async def get_system_analytics(self, days: int = 30) -> SystemAnalytics:
        """Get overall system analytics"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # User counts
        total_users = await self.db.users.count_documents({"is_active": True})
        active_subscribers = await self.db.users.count_documents({
            "is_active": True,
            "subscription_tier": {"$ne": "free"}
        })
        
        # API usage
        total_api_calls = await self.db.api_usage.count_documents({
            "timestamp": {"$gte": start_date}
        })
        
        # Daily active users
        daily_active_users = await self.db.api_usage.distinct("user_id", {
            "timestamp": {"$gte": datetime.utcnow() - timedelta(days=1)},
            "user_id": {"$ne": None}
        })
        
        # Revenue calculation (estimated)
        pro_users = await self.db.users.count_documents({
            "subscription_tier": "pro",
            "is_active": True
        })
        business_users = await self.db.users.count_documents({
            "subscription_tier": "business", 
            "is_active": True
        })
        
        revenue_this_month = (pro_users * 9.99) + (business_users * 29.99)
        
        # Platform distribution
        platform_pipeline = [
            {"$match": {"fetched_at": {"$gte": start_date}}},
            {"$group": {"_id": "$platform", "count": {"$sum": 1}}}
        ]
        
        platform_results = await self.db.viral_videos.aggregate(platform_pipeline).to_list(10)
        platform_distribution = {
            Platform(result["_id"]): result["count"] 
            for result in platform_results 
            if result["_id"] in Platform.__members__.values()
        }
        
        return SystemAnalytics(
            total_users=total_users,
            total_api_calls=total_api_calls,
            revenue_this_month=round(revenue_this_month, 2),
            active_subscribers=active_subscribers,
            platform_distribution=platform_distribution,
            daily_active_users=len(daily_active_users)
        )
    
    async def get_revenue_analytics(self, days: int = 30) -> Dict:
        """Get detailed revenue analytics"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Payment transactions
        payments = await self.db.payment_transactions.find({
            "created_at": {"$gte": start_date},
            "status": "completed"
        }).to_list(10000)
        
        # Group by subscription tier
        revenue_by_tier = {"pro": 0.0, "business": 0.0}
        for payment in payments:
            tier = payment.get("subscription_tier")
            if tier in revenue_by_tier:
                revenue_by_tier[tier] += payment.get("amount", 0.0)
        
        # Daily revenue
        daily_revenue = {}
        for payment in payments:
            date_str = payment["created_at"].strftime("%Y-%m-%d")
            daily_revenue[date_str] = daily_revenue.get(date_str, 0.0) + payment.get("amount", 0.0)
        
        total_revenue = sum(daily_revenue.values())
        
        return {
            "total_revenue": round(total_revenue, 2),
            "revenue_by_tier": revenue_by_tier,
            "daily_revenue": daily_revenue,
            "average_daily_revenue": round(total_revenue / days, 2) if days > 0 else 0,
            "total_transactions": len(payments)
        }
    
    async def create_analytics_dashboard_data(self, user_id: Optional[str] = None) -> Dict:
        """Create comprehensive dashboard data"""
        
        # System analytics
        system_analytics = await self.get_system_analytics()
        platform_analytics = await self.get_platform_analytics()
        revenue_analytics = await self.get_revenue_analytics()
        
        dashboard_data = {
            "system": system_analytics.dict(),
            "platforms": platform_analytics,
            "revenue": revenue_analytics,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Add user-specific analytics if user_id provided
        if user_id:
            user_analytics = await self.get_user_analytics(user_id)
            dashboard_data["user"] = user_analytics.dict()
        
        return dashboard_data