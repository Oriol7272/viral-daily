from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
import aiohttp
import asyncio
from enum import Enum
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import re

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="Viral Daily API", description="API for aggregating viral videos from multiple platforms")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

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

# Data Models
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
    viral_score: float = 0.0  # Custom scoring algorithm
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    published_at: Optional[datetime] = None

class VideoResponse(BaseModel):
    videos: List[ViralVideo]
    total: int
    platform: Optional[Platform] = None
    date: datetime

class Subscription(BaseModel):
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

# Video Aggregation Service
class VideoAggregator:
    def __init__(self):
        self.youtube_api_key = os.getenv('YOUTUBE_API_KEY')
        self.twitter_bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
        self.tiktok_access_token = os.getenv('TIKTOK_ACCESS_TOKEN')
        self.instagram_access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN')
        
    def get_youtube_service(self):
        """Initialize YouTube API service"""
        if not self.youtube_api_key:
            return None
        try:
            return build('youtube', 'v3', developerKey=self.youtube_api_key, cache_discovery=False)
        except Exception as e:
            logging.error(f"Failed to initialize YouTube service: {e}")
            return None
            
    def parse_duration(self, duration: str) -> str:
        """Parse YouTube duration format PT1M30S to readable format"""
        if not duration:
            return "0:00"
        
        match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
        if not match:
            return "0:00"
        
        hours, minutes, seconds = match.groups()
        hours = int(hours) if hours else 0
        minutes = int(minutes) if minutes else 0
        seconds = int(seconds) if seconds else 0
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes}:{seconds:02d}"
    
    def calculate_viral_score(self, views: int, likes: int, days_old: int) -> float:
        """Calculate viral score based on engagement and recency"""
        if not views or views == 0:
            return 0.0
        
        # Base score from view count (logarithmic scale)
        import math
        view_score = math.log10(max(views, 1)) * 10
        
        # Engagement ratio (likes per view)
        engagement_ratio = (likes / views) if likes and views > 0 else 0
        engagement_score = engagement_ratio * 100
        
        # Recency bonus (more recent = higher score)
        recency_multiplier = max(1.0, 10.0 - (days_old * 0.5))
        
        # Final viral score
        viral_score = (view_score + engagement_score) * recency_multiplier
        return min(viral_score, 100.0)  # Cap at 100

    async def fetch_youtube_viral_videos(self, limit: int = 10) -> List[ViralVideo]:
        """Fetch real viral videos from YouTube"""
        videos = []
        
        youtube = self.get_youtube_service()
        if not youtube:
            logging.warning("YouTube API not available, returning mock data")
            return await self._get_youtube_mock_data(limit)
        
        try:
            # Get trending videos
            trending_request = youtube.videos().list(
                part='snippet,statistics,contentDetails',
                chart='mostPopular',
                regionCode='US',
                maxResults=limit,
                videoCategoryId='0'  # All categories
            )
            trending_response = trending_request.execute()
            
            for item in trending_response.get('items', []):
                try:
                    snippet = item['snippet']
                    statistics = item['statistics']
                    content_details = item['contentDetails']
                    
                    # Extract data
                    video_id = item['id']
                    title = snippet.get('title', 'Untitled')
                    channel_title = snippet.get('channelTitle', 'Unknown Channel')
                    published_at = datetime.fromisoformat(snippet['publishedAt'].replace('Z', '+00:00'))
                    
                    # Statistics
                    views = int(statistics.get('viewCount', 0))
                    likes = int(statistics.get('likeCount', 0))
                    
                    # Duration
                    duration = self.parse_duration(content_details.get('duration', ''))
                    
                    # Calculate days since publication
                    days_old = (datetime.now(published_at.tzinfo) - published_at).days
                    
                    # Calculate viral score
                    viral_score = self.calculate_viral_score(views, likes, days_old)
                    
                    # Get best thumbnail
                    thumbnails = snippet.get('thumbnails', {})
                    thumbnail_url = (thumbnails.get('maxresdefault', {}).get('url') or
                                   thumbnails.get('standard', {}).get('url') or
                                   thumbnails.get('high', {}).get('url') or
                                   thumbnails.get('medium', {}).get('url') or
                                   thumbnails.get('default', {}).get('url', ''))
                    
                    video = ViralVideo(
                        title=title,
                        url=f"https://www.youtube.com/watch?v={video_id}",
                        thumbnail=thumbnail_url,
                        platform=Platform.YOUTUBE,
                        views=views,
                        likes=likes,
                        author=channel_title,
                        duration=duration,
                        description=snippet.get('description', '')[:200] + '...' if snippet.get('description') else '',
                        viral_score=viral_score,
                        published_at=published_at.replace(tzinfo=None)
                    )
                    videos.append(video)
                    
                except Exception as e:
                    logging.error(f"Error processing YouTube video: {e}")
                    continue
            
            # Sort by viral score
            videos.sort(key=lambda x: x.viral_score, reverse=True)
            
        except HttpError as e:
            logging.error(f"YouTube API error: {e}")
            if "quotaExceeded" in str(e):
                logging.warning("YouTube API quota exceeded, returning mock data")
            elif "keyInvalid" in str(e) or "API key not valid" in str(e):
                logging.warning("YouTube API key invalid, returning mock data")
            else:
                logging.warning(f"YouTube API error: {str(e)}, returning mock data")
            return await self._get_youtube_mock_data(limit)
        except Exception as e:
            logging.error(f"Unexpected error fetching YouTube videos: {e}")
            return await self._get_youtube_mock_data(limit)
            
        return videos[:limit]

    async def _get_youtube_mock_data(self, limit: int) -> List[ViralVideo]:
        """Fallback mock data for YouTube"""
        videos = []
        for i in range(limit):
            video = ViralVideo(
                title=f"YouTube Viral Video {i+1}",
                url=f"https://www.youtube.com/watch?v=mock{i+1}",
                thumbnail=f"https://img.youtube.com/vi/mock{i+1}/maxresdefault.jpg",
                platform=Platform.YOUTUBE,
                views=1000000 + i * 100000,
                likes=50000 + i * 5000,
                author=f"Creator {i+1}",
                duration=f"{2+i}:{30+i:02d}",
                viral_score=90.0 - i * 2,
                published_at=datetime.utcnow() - timedelta(hours=i)
            )
            videos.append(video)
        return videos

    async def fetch_tiktok_viral_videos(self, limit: int = 10) -> List[ViralVideo]:
        """Fetch viral videos from TikTok - Enhanced mock data for now"""
        videos = []
        
        # Enhanced mock data with more realistic titles and stats
        tiktok_titles = [
            "POV: You finally understand the assignment 😭",
            "This trend is everywhere but I did it better 💅",
            "Tell me you're Gen Z without telling me you're Gen Z",
            "Plot twist: Nobody saw this coming 🤯",
            "The way I ran to try this trend...",
            "This is why I don't trust anyone anymore",
            "When the beat drops and you know it's your moment",
            "Rating viral foods until I find the best one",
            "The audacity of this generation amazes me",
            "Can we normalize this please? 🙏"
        ]
        
        for i in range(limit):
            video = ViralVideo(
                title=tiktok_titles[i % len(tiktok_titles)],
                url=f"https://www.tiktok.com/@viraluser{i+1}/video/7{i+1:012d}",
                thumbnail=f"https://via.placeholder.com/300x400/FF0050/FFFFFF?text=TikTok+{i+1}",
                platform=Platform.TIKTOK,
                views=5000000 + i * 200000,
                likes=250000 + i * 10000,
                author=f"@tiktoker{i+1}",
                duration=f"0:{15+i:02d}",
                viral_score=85.0 - i * 1.5,
                published_at=datetime.utcnow() - timedelta(hours=i * 2)
            )
            videos.append(video)
            
        return videos

    async def fetch_twitter_viral_videos(self, limit: int = 10) -> List[ViralVideo]:
        """Fetch viral videos from Twitter/X - Enhanced mock data"""
        videos = []
        
        twitter_titles = [
            "This video has me CRYING 😂😂😂",
            "Twitter do your thing and make this viral",
            "The internet is undefeated with these memes",
            "POV: You open Twitter and see this",
            "This tweet aged like fine wine",
            "The way Twitter came together for this...",
            "Breaking: This video broke the internet",
            "When Twitter users unite for something wholesome",
            "This thread explains everything perfectly",
            "Twitter main character of the day:"
        ]
        
        for i in range(limit):
            video = ViralVideo(
                title=twitter_titles[i % len(twitter_titles)],
                url=f"https://twitter.com/viraltweets/status/17{i+1:014d}",
                thumbnail=f"https://via.placeholder.com/400x225/1DA1F2/FFFFFF?text=Twitter+{i+1}",
                platform=Platform.TWITTER,
                views=2000000 + i * 150000,
                likes=100000 + i * 8000,
                shares=25000 + i * 2000,
                author=f"@twitteruser{i+1}",
                viral_score=80.0 - i * 1.8,
                published_at=datetime.utcnow() - timedelta(hours=i * 3)
            )
            videos.append(video)
            
        return videos

    async def fetch_instagram_viral_videos(self, limit: int = 10) -> List[ViralVideo]:
        """Fetch viral videos from Instagram - Enhanced mock data"""
        videos = []
        
        instagram_titles = [
            "This Reel is giving main character energy ✨",
            "POV: You're living your best life",
            "The aesthetic is immaculate 📸",
            "This trend but make it fashion 💫",
            "Caught in 4K being absolutely iconic",
            "The vibes are unmatched in this one",
            "This Reel said 'I'm that girl' 💅",
            "When the algorithm knows exactly what you need",
            "This is peak content creation right here",
            "The way this Reel understood the assignment"
        ]
        
        for i in range(limit):
            video = ViralVideo(
                title=instagram_titles[i % len(instagram_titles)],
                url=f"https://www.instagram.com/reel/C{i+1:010d}/",
                thumbnail=f"https://via.placeholder.com/300x300/E4405F/FFFFFF?text=IG+{i+1}",
                platform=Platform.INSTAGRAM,
                views=3000000 + i * 180000,
                likes=180000 + i * 9000,
                author=f"@instagrammer{i+1}",
                viral_score=88.0 - i * 2.2,
                published_at=datetime.utcnow() - timedelta(hours=i * 1.5)
            )
            videos.append(video)
            
        return videos

    async def get_aggregated_viral_videos(self, limit: int = 40) -> List[ViralVideo]:
        """Get viral videos from all platforms and sort by viral score"""
        all_videos = []
        
        # Fetch from all platforms concurrently
        tasks = [
            self.fetch_youtube_viral_videos(limit // 4),
            self.fetch_tiktok_viral_videos(limit // 4),
            self.fetch_twitter_viral_videos(limit // 4),
            self.fetch_instagram_viral_videos(limit // 4)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, list):
                all_videos.extend(result)
            else:
                logging.error(f"Error fetching platform videos: {result}")
        
        # Sort by viral score and return top videos
        all_videos.sort(key=lambda x: x.viral_score, reverse=True)
        return all_videos[:limit]

# Initialize aggregator
aggregator = VideoAggregator()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Viral Daily API - Aggregating the most viral content from across the web!"}

@api_router.get("/videos", response_model=VideoResponse)
async def get_viral_videos(platform: Optional[Platform] = None, limit: int = 10):
    """Get viral videos from all platforms or a specific platform"""
    try:
        if platform:
            # Get videos from specific platform
            if platform == Platform.YOUTUBE:
                videos = await aggregator.fetch_youtube_viral_videos(limit)
            elif platform == Platform.TIKTOK:
                videos = await aggregator.fetch_tiktok_viral_videos(limit)
            elif platform == Platform.TWITTER:
                videos = await aggregator.fetch_twitter_viral_videos(limit)
            elif platform == Platform.INSTAGRAM:
                videos = await aggregator.fetch_instagram_viral_videos(limit)
            else:
                videos = []
        else:
            # Get aggregated videos from all platforms
            videos = await aggregator.get_aggregated_viral_videos(limit)
        
        # Store videos in database for future reference
        for video in videos:
            try:
                await db.viral_videos.update_one(
                    {"url": video.url},
                    {"$set": video.dict()},
                    upsert=True
                )
            except Exception as e:
                logger.error(f"Error storing video {video.url}: {e}")
        
        return VideoResponse(
            videos=videos,
            total=len(videos),
            platform=platform,
            date=datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"Error fetching videos: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching viral videos")

@api_router.get("/videos/history")
async def get_video_history(days: int = 7, platform: Optional[Platform] = None):
    """Get historical viral videos from the database"""
    try:
        filter_query = {
            "fetched_at": {
                "$gte": datetime.utcnow() - timedelta(days=days)
            }
        }
        
        if platform:
            filter_query["platform"] = platform.value
        
        videos = await db.viral_videos.find(filter_query).sort("viral_score", -1).to_list(100)
        return {"videos": videos, "total": len(videos)}
    except Exception as e:
        logger.error(f"Error fetching video history: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching video history")

@api_router.post("/subscribe", response_model=Subscription)
async def create_subscription(subscription_data: SubscriptionCreate):
    """Create a new subscription for daily viral video delivery"""
    try:
        subscription = Subscription(**subscription_data.dict())
        await db.subscriptions.insert_one(subscription.dict())
        return subscription
    except Exception as e:
        logger.error(f"Error creating subscription: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating subscription")

@api_router.get("/subscriptions")
async def get_subscriptions():
    """Get all active subscriptions"""
    try:
        subscriptions = await db.subscriptions.find({"active": True}).to_list(1000)
        return {"subscriptions": subscriptions, "total": len(subscriptions)}
    except Exception as e:
        logger.error(f"Error fetching subscriptions: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching subscriptions")

@api_router.post("/deliver-daily")
async def deliver_daily_videos(background_tasks: BackgroundTasks):
    """Trigger daily delivery of viral videos to subscribers"""
    try:
        # Get today's top viral videos
        videos = await aggregator.get_aggregated_viral_videos(10)
        
        # Get active subscriptions
        subscriptions = await db.subscriptions.find({"active": True}).to_list(1000)
        
        # Schedule delivery for each subscriber
        for subscription in subscriptions:
            background_tasks.add_task(deliver_to_subscriber, subscription, videos)
        
        return {"message": f"Daily delivery scheduled for {len(subscriptions)} subscribers"}
    except Exception as e:
        logger.error(f"Error scheduling daily delivery: {str(e)}")
        raise HTTPException(status_code=500, detail="Error scheduling daily delivery")

async def deliver_to_subscriber(subscription: dict, videos: List[ViralVideo]):
    """Deliver videos to a specific subscriber"""
    try:
        # TODO: Implement actual delivery logic
        # For now, just log the delivery
        logger.info(f"Delivering {len(videos)} videos to subscriber {subscription['id']}")
        
        # Update last delivery timestamp
        await db.subscriptions.update_one(
            {"id": subscription["id"]},
            {"$set": {"last_delivery": datetime.utcnow()}}
        )
    except Exception as e:
        logger.error(f"Error delivering to subscriber {subscription.get('id')}: {str(e)}")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()