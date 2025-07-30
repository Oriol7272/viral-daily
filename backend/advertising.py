# Advertising System

from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from models import Advertisement, AdImpression, AdClick, Platform, User, SubscriptionTier, ViralVideo
import random
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class AdvertisingService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    async def get_ads_for_platform(self, platform: Optional[Platform] = None, 
                                 user: Optional[User] = None, limit: int = 3) -> List[Advertisement]:
        """Get relevant ads for a platform and user"""
        
        # Premium users don't see ads
        if user and user.subscription_tier != SubscriptionTier.FREE:
            return []
        
        # Build query
        query = {"is_active": True}
        if platform:
            query["target_platforms"] = {"$in": [platform.value]}
        
        # Get active ads
        ads_cursor = self.db.advertisements.find(query).limit(limit)
        ads = await ads_cursor.to_list(limit)
        
        # Convert to Advertisement objects
        ad_objects = []
        for ad_data in ads:
            try:
                ad = Advertisement(**ad_data)
                ad_objects.append(ad)
            except Exception as e:
                logger.error(f"Error parsing advertisement: {e}")
                continue
        
        return ad_objects
    
    async def record_impression(self, ad_id: str, user: Optional[User] = None, 
                              platform: Optional[Platform] = None) -> bool:
        """Record an ad impression"""
        try:
            impression = AdImpression(
                ad_id=ad_id,
                user_id=user.id if user else None,
                platform=platform
            )
            
            # Save impression
            await self.db.ad_impressions.insert_one(impression.dict())
            
            # Update ad impression count
            await self.db.advertisements.update_one(
                {"id": ad_id},
                {"$inc": {"impressions": 1}}
            )
            
            return True
        except Exception as e:
            logger.error(f"Error recording ad impression: {e}")
            return False
    
    async def record_click(self, ad_id: str, user: Optional[User] = None) -> bool:
        """Record an ad click and calculate revenue"""
        try:
            # Get ad details for revenue calculation
            ad_data = await self.db.advertisements.find_one({"id": ad_id})
            if not ad_data:
                return False
            
            ad = Advertisement(**ad_data)
            
            # Record click
            click = AdClick(
                ad_id=ad_id,
                user_id=user.id if user else None,
                revenue=ad.cost_per_click
            )
            
            await self.db.ad_clicks.insert_one(click.dict())
            
            # Update ad click count
            await self.db.advertisements.update_one(
                {"id": ad_id},
                {"$inc": {"clicks": 1}}
            )
            
            return True
        except Exception as e:
            logger.error(f"Error recording ad click: {e}")
            return False
    
    async def create_sample_ads(self):
        """Create sample advertisements for testing"""
        sample_ads = [
            {
                "title": "Boost Your Social Media Presence",
                "description": "Get more followers and engagement with our proven strategies",
                "image_url": "https://via.placeholder.com/300x200/4285F4/FFFFFF?text=Social+Media+Boost",
                "click_url": "https://example.com/social-media-boost",
                "advertiser": "SocialGrow Pro",
                "target_platforms": ["youtube", "twitter", "tiktok"],
                "budget": 1000.0,
                "cost_per_click": 0.50,
                "is_active": True
            },
            {
                "title": "Learn Video Editing Like a Pro",
                "description": "Master video editing with our comprehensive online course",
                "image_url": "https://via.placeholder.com/300x200/FF5722/FFFFFF?text=Video+Editing+Course",
                "click_url": "https://example.com/video-editing-course",
                "advertiser": "EduTech Academy",
                "target_platforms": ["youtube", "tiktok"],
                "budget": 750.0,
                "cost_per_click": 0.75,
                "is_active": True
            },
            {
                "title": "Viral Content Creation Tools",
                "description": "Create viral content with our AI-powered tools and templates",
                "image_url": "https://via.placeholder.com/300x200/9C27B0/FFFFFF?text=Content+Tools",
                "click_url": "https://example.com/content-creation-tools",
                "advertiser": "ViralMaker AI",
                "target_platforms": ["youtube", "twitter", "tiktok"],
                "budget": 1500.0,
                "cost_per_click": 1.00,
                "is_active": True
            },
            {
                "title": "Grow Your Brand with Influencers",
                "description": "Connect with top influencers to amplify your brand message",
                "image_url": "https://via.placeholder.com/300x200/E91E63/FFFFFF?text=Influencer+Marketing",
                "click_url": "https://example.com/influencer-marketing",
                "advertiser": "InfluenceHub",
                "target_platforms": ["instagram", "youtube"],
                "budget": 2000.0,
                "cost_per_click": 1.25,
                "is_active": True
            }
        ]
        
        for ad_data in sample_ads:
            ad = Advertisement(**ad_data)
            
            # Check if ad already exists
            existing = await self.db.advertisements.find_one({"title": ad.title})
            if not existing:
                await self.db.advertisements.insert_one(ad.dict())
                logger.info(f"Created sample ad: {ad.title}")
    
    async def get_ad_analytics(self, advertiser: Optional[str] = None, days: int = 30) -> dict:
        """Get advertising analytics"""
        from datetime import timedelta
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Build query
        match_query = {"timestamp": {"$gte": start_date}}
        
        # Get impression analytics
        impression_pipeline = [
            {"$match": match_query},
            {"$group": {
                "_id": "$ad_id",
                "impressions": {"$sum": 1}
            }}
        ]
        
        impressions = await self.db.ad_impressions.aggregate(impression_pipeline).to_list(1000)
        
        # Get click analytics
        click_pipeline = [
            {"$match": match_query},
            {"$group": {
                "_id": "$ad_id",
                "clicks": {"$sum": 1},
                "revenue": {"$sum": "$revenue"}
            }}
        ]
        
        clicks = await self.db.ad_clicks.aggregate(click_pipeline).to_list(1000)
        
        # Combine data
        analytics = {}
        for item in impressions:
            ad_id = item["_id"]
            analytics[ad_id] = {"impressions": item["impressions"], "clicks": 0, "revenue": 0.0}
        
        for item in clicks:
            ad_id = item["_id"]
            if ad_id in analytics:
                analytics[ad_id]["clicks"] = item["clicks"]
                analytics[ad_id]["revenue"] = item["revenue"]
            else:
                analytics[ad_id] = {"impressions": 0, "clicks": item["clicks"], "revenue": item["revenue"]}
        
        # Calculate totals
        total_impressions = sum(data["impressions"] for data in analytics.values())
        total_clicks = sum(data["clicks"] for data in analytics.values())
        total_revenue = sum(data["revenue"] for data in analytics.values())
        
        return {
            "total_impressions": total_impressions,
            "total_clicks": total_clicks,
            "total_revenue": round(total_revenue, 2),
            "ctr": round((total_clicks / total_impressions * 100) if total_impressions > 0 else 0, 2),
            "by_ad": analytics
        }
    
    def inject_ads_into_videos(self, videos: List, ads: List[Advertisement], 
                              user: Optional[User] = None) -> List:
        """Inject ads into video list for free tier users"""
        
        # Premium users don't see ads
        if user and user.subscription_tier != SubscriptionTier.FREE:
            return videos
        
        if not ads or len(videos) < 4:
            return videos
        
        # Insert ads every 5-8 videos
        result = []
        ad_index = 0
        
        for i, video in enumerate(videos):
            result.append(video)
            
            # Insert ad every 6-8 videos (with some randomness)
            if (i + 1) % random.randint(6, 8) == 0 and ad_index < len(ads):
                ad = ads[ad_index]
                # Create ViralVideo object for ads instead of dict
                ad_video = ViralVideo(
                    id=f"ad_{ad.id}",
                    title=f"🎯 {ad.title}",
                    url=ad.click_url,
                    thumbnail=ad.image_url,
                    platform="advertisement",
                    views=None,
                    likes=None,
                    author=ad.advertiser,
                    description=ad.description,
                    viral_score=0,
                    is_sponsored=True,
                    sponsor_name=ad.advertiser,
                    fetched_at=datetime.utcnow(),
                    published_at=datetime.utcnow()
                )
                result.append(ad_video)
                ad_index += 1
        
        return result