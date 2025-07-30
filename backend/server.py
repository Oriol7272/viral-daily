from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks, Depends, Request, Header
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
import aiohttp
import asyncio
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import re
import time

# Import monetization modules
from models import *
from auth import AuthService, get_current_user, require_user, require_pro_user, require_business_user
from subscription_plans import SUBSCRIPTION_PLANS, get_plan, get_stripe_price_id
from advertising import AdvertisingService
from analytics import AnalyticsService
from payments import create_payment_router
from paypal_integration import create_paypal_router

# Stripe integration
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Initialize services
auth_service = AuthService(db)
advertising_service = AdvertisingService(db)
analytics_service = AnalyticsService(db)

# Stripe setup
stripe_api_key = os.environ.get('STRIPE_API_KEY')

# Create the main app
app = FastAPI(title="Viral Daily API", description="Monetized API for aggregating viral videos from multiple platforms")

# Create routers
api_router = APIRouter(prefix="/api")
payments_router = create_payment_router(db, auth_service)
paypal_router = create_paypal_router(db)
admin_router = APIRouter(prefix="/api/admin")

# Video Aggregation Service (Enhanced)
class VideoAggregator:
    def __init__(self):
        self.youtube_api_key = os.getenv('YOUTUBE_API_KEY')
        self.twitter_bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
        self.tiktok_access_token = os.getenv('TIKTOK_ACCESS_TOKEN')
        
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
    
    def generate_platform_thumbnail(self, platform: Platform, viral_score: float, title: str = "") -> str:
        """Generate SVG thumbnail for platforms without real thumbnails"""
        from urllib.parse import quote
        
        # Platform-specific colors and icons
        platform_config = {
            Platform.TIKTOK: {
                'color': '#000000',
                'icon': '🎵',
                'name': 'TIKTOK'
            },
            Platform.TWITTER: {
                'color': '#1DA1F2',
                'icon': '🐦',
                'name': 'TWITTER'
            },
            Platform.YOUTUBE: {
                'color': '#FF0000',
                'icon': '📺',
                'name': 'YOUTUBE'
            }
        }
        
        config = platform_config.get(platform, {
            'color': '#6B7280',
            'icon': '🎬',
            'name': 'VIDEO'
        })
        
        # Truncate title for thumbnail
        display_title = (title[:30] + "...") if len(title) > 30 else title
        score = int(viral_score) if viral_score else 0
        
        # Generate clean SVG
        svg_content = f'''<svg width="400" height="225" xmlns="http://www.w3.org/2000/svg">
            <rect width="400" height="225" fill="{config['color']}"/>
            <rect x="0" y="0" width="400" height="225" fill="url(#grad1)" opacity="0.1"/>
            <defs>
                <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:white;stop-opacity:0.3" />
                    <stop offset="100%" style="stop-color:white;stop-opacity:0" />
                </linearGradient>
            </defs>
            <text x="200" y="80" text-anchor="middle" fill="white" font-size="40" font-weight="bold">{config['icon']}</text>
            <text x="200" y="110" text-anchor="middle" fill="white" font-size="20" font-weight="bold">{config['name']}</text>
            <text x="200" y="135" text-anchor="middle" fill="white" font-size="16" opacity="0.9">Viral Score: {score}</text>
            <text x="200" y="160" text-anchor="middle" fill="white" font-size="12" opacity="0.7">VIRAL DAILY</text>
            <rect x="10" y="190" width="380" height="25" fill="rgba(255,255,255,0.1)" rx="5"/>
            <text x="200" y="207" text-anchor="middle" fill="white" font-size="11" opacity="0.8">{display_title}</text>
        </svg>'''
        
        # Return as data URI
        return f"data:image/svg+xml;charset=utf-8,{quote(svg_content)}"

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
        
        # Use real YouTube thumbnail URLs from popular videos
        real_thumbnails = [
            "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",  # Never Gonna Give You Up
            "https://i.ytimg.com/vi/9bZkp7q19f0/maxresdefault.jpg",  # Gangnam Style
            "https://i.ytimg.com/vi/kJQP7kiw5Fk/maxresdefault.jpg",  # Despacito
            "https://i.ytimg.com/vi/fJ9rUzIMcZQ/maxresdefault.jpg",  # Shape of You
            "https://i.ytimg.com/vi/YQHsXMglC9A/maxresdefault.jpg",  # Hello - Adele
            "https://i.ytimg.com/vi/CevxZvSJLk8/maxresdefault.jpg",  # Roar - Katy Perry
            "https://i.ytimg.com/vi/RgKAFK5djSk/maxresdefault.jpg",  # Wrecking Ball
            "https://i.ytimg.com/vi/hT_nvWreIhg/maxresdefault.jpg",  # Counting Stars
            "https://i.ytimg.com/vi/iGk5fR-t5AU/maxresdefault.jpg",  # Firework
            "https://i.ytimg.com/vi/nfWlot6h_JM/maxresdefault.jpg"   # Shake It Off
        ]
        
        youtube_titles = [
            "This Video Will Change Your Perspective Forever 🤯",
            "The Most Satisfying Video You'll Ever Watch",
            "Everyone's Talking About This Viral Dance Challenge",
            "This Trick Will Blow Your Mind! (Not Clickbait)",
            "Why This Song is Breaking the Internet",
            "The Funniest Video That's Taking Over YouTube",
            "This Life Hack Changed Everything For Me",
            "The Most Wholesome Video on the Internet Right Now",
            "This Performance Gave Me Chills - Pure Talent!",
            "Watch This Before It Gets Taken Down!"
        ]
        
        for i in range(limit):
            video = ViralVideo(
                title=youtube_titles[i % len(youtube_titles)],
                url=f"https://www.youtube.com/watch?v=viral{i+1:03d}",
                thumbnail=real_thumbnails[i % len(real_thumbnails)],
                platform=Platform.YOUTUBE,
                views=1000000 + i * 100000,
                likes=50000 + i * 5000,
                author=f"ViralCreator{i+1}",
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
        
        # Use data URIs for TikTok thumbnails to avoid external dependencies
        for i in range(limit):
            viral_score = 85.0 - i * 1.5
            title = tiktok_titles[i % len(tiktok_titles)]
            
            video = ViralVideo(
                title=title,
                url=f"https://www.tiktok.com/@viraluser{i+1}/video/7{i+1:012d}",
                thumbnail=self.generate_platform_thumbnail(Platform.TIKTOK, viral_score, title),
                platform=Platform.TIKTOK,
                views=5000000 + i * 200000,
                likes=250000 + i * 10000,
                author=f"@tiktoker{i+1}",
                duration=f"0:{15+i:02d}",
                viral_score=viral_score,
                published_at=datetime.utcnow() - timedelta(hours=i * 2)
            )
            videos.append(video)
            
        return videos

    async def _get_twitter_mock_data(self, limit: int) -> List[ViralVideo]:
        """Enhanced mock data for Twitter"""
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
        
        videos = []
        for i in range(limit):
            viral_score = 80.0 - i * 1.8
            title = twitter_titles[i % len(twitter_titles)]
            
            video = ViralVideo(
                title=title,
                url=f"https://twitter.com/viraltweets/status/17{i+1:014d}",
                thumbnail=self.generate_platform_thumbnail(Platform.TWITTER, viral_score, title),
                platform=Platform.TWITTER,
                views=2000000 + i * 150000,
                likes=100000 + i * 8000,
                shares=25000 + i * 2000,
                author=f"@twitteruser{i+1}",
                viral_score=viral_score,
                published_at=datetime.utcnow() - timedelta(hours=i * 3)
            )
            videos.append(video)
        return videos

    async def fetch_twitter_viral_videos(self, limit: int = 10) -> List[ViralVideo]:
        """Fetch viral videos from Twitter/X using API v2"""
        videos = []
        
        if not self.twitter_bearer_token:
            logging.warning("Twitter Bearer token not available, returning enhanced mock data")
            return await self._get_twitter_mock_data(limit)
        
        try:
            import tweepy
            
            # Initialize Twitter API client
            client = tweepy.Client(bearer_token=self.twitter_bearer_token)
            
            # Search for tweets with videos that have high engagement
            search_query = "(has:videos OR has:media) -is:retweet min_faves:1000 lang:en"
            
            tweets = client.search_recent_tweets(
                query=search_query,
                max_results=min(limit, 100),  # API limit
                tweet_fields=['created_at', 'public_metrics', 'author_id', 'attachments'],
                media_fields=['url', 'preview_image_url', 'type', 'duration_ms'],
                expansions=['attachments.media_keys', 'author_id'],
                user_fields=['username', 'name']
            )
            
            if not tweets.data:
                logging.warning("No Twitter data found, returning mock data")
                return await self._get_twitter_mock_data(limit)
            
            # Process tweets
            for tweet in tweets.data[:limit]:
                try:
                    metrics = tweet.public_metrics
                    
                    # Get author info
                    author_username = "Unknown"
                    if tweets.includes and 'users' in tweets.includes:
                        for user in tweets.includes['users']:
                            if user.id == tweet.author_id:
                                author_username = f"@{user.username}"
                                break
                    
                    # Calculate viral score
                    likes = metrics['like_count']
                    retweets = metrics['retweet_count']
                    replies = metrics['reply_count']
                    
                    # Twitter viral score calculation
                    engagement_score = likes + (retweets * 3) + (replies * 2)
                    viral_score = min(90.0, max(10.0, engagement_score / 1000))
                    
                    # Create video object
                    video = ViralVideo(
                        title=tweet.text[:100] + "..." if len(tweet.text) > 100 else tweet.text,
                        url=f"https://twitter.com/i/status/{tweet.id}",
                        thumbnail="", # Will trigger fallback to SVG placeholder
                        platform=Platform.TWITTER,
                        views=metrics.get('impression_count', 0),
                        likes=likes,
                        shares=retweets,
                        author=author_username,
                        viral_score=viral_score,
                        published_at=tweet.created_at.replace(tzinfo=None) if tweet.created_at else datetime.utcnow()
                    )
                    videos.append(video)
                    
                except Exception as e:
                    logging.error(f"Error processing Twitter tweet: {e}")
                    continue
                    
        except Exception as e:
            logging.error(f"Twitter API error: {e}")
            logging.warning("Falling back to Twitter mock data")
            return await self._get_twitter_mock_data(limit)
        
        # Sort by viral score
        videos.sort(key=lambda x: x.viral_score, reverse=True)
        return videos



    async def get_aggregated_viral_videos(self, limit: int = 40, user: Optional[User] = None) -> List[ViralVideo]:
        """Get viral videos from all platforms and sort by viral score"""
        
        # Apply user tier limits
        if user:
            plan = get_plan(user.subscription_tier)
            if plan.max_videos_per_day > 0:
                limit = min(limit, plan.max_videos_per_day)
        else:
            # Anonymous users get free tier limits
            free_plan = get_plan(SubscriptionTier.FREE)
            limit = min(limit, free_plan.max_videos_per_day)
        
        all_videos = []
        
        # Fetch from all platforms concurrently
        tasks = [
            self.fetch_youtube_viral_videos(limit // 3),
            self.fetch_tiktok_viral_videos(limit // 3),
            self.fetch_twitter_viral_videos(limit // 3)
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

# Middleware to track API usage
@app.middleware("http")
async def track_api_usage_middleware(request: Request, call_next):
    start_time = time.time()
    
    # Get current user if available
    api_key = None
    if "authorization" in request.headers:
        auth_header = request.headers["authorization"]
        if auth_header.startswith("Bearer "):
            api_key = auth_header.split(" ")[1]
    elif "x-api-key" in request.headers:
        api_key = request.headers["x-api-key"]
    
    user = None
    if api_key:
        user = await auth_service.get_user_by_api_key(api_key)
    
    # Process request
    response = await call_next(request)
    
    # Calculate response time
    process_time = time.time() - start_time
    response_time_ms = process_time * 1000
    
    # Log API usage (async)
    if request.url.path.startswith("/api/"):
        asyncio.create_task(
            auth_service.log_api_usage(
                user=user,
                endpoint=str(request.url.path),
                method=request.method,
                api_key=api_key,
                response_time_ms=response_time_ms,
                status_code=response.status_code
            )
        )
    
    return response

# Core API Routes
@api_router.get("/")
async def root():
    return {
        "message": "Viral Daily API - Monetized viral content aggregation",
        "version": "2.0",
        "features": ["Premium Subscriptions", "API Access", "Analytics", "No Ads for Premium"],
        "subscription_tiers": list(SUBSCRIPTION_PLANS.keys())
    }

@api_router.get("/videos", response_model=VideoResponse)
async def get_viral_videos(
    platform: Optional[Platform] = None, 
    limit: int = 10,
    user: Optional[User] = Depends(get_current_user),
    request: Request = None
):
    """Get viral videos from all platforms or a specific platform"""
    try:
        # Check rate limits
        if user and not await auth_service.check_api_rate_limit(user):
            raise HTTPException(
                status_code=429, 
                detail="API rate limit exceeded. Upgrade to Pro for higher limits."
            )
        
        # Get user's plan
        user_plan = get_plan(user.subscription_tier if user else SubscriptionTier.FREE)
        
        # Apply limits based on subscription
        max_limit = user_plan.max_videos_per_day if user_plan.max_videos_per_day > 0 else limit
        limit = min(limit, max_limit)
        
        if platform:
            # Get videos from specific platform
            if platform == Platform.YOUTUBE:
                videos = await aggregator.fetch_youtube_viral_videos(limit)
            elif platform == Platform.TIKTOK:
                videos = await aggregator.fetch_tiktok_viral_videos(limit)
            elif platform == Platform.TWITTER:
                videos = await aggregator.fetch_twitter_viral_videos(limit)
            else:
                videos = []
        else:
            # Get aggregated videos from all platforms
            videos = await aggregator.get_aggregated_viral_videos(limit, user)
        
        # Get ads for free tier users
        ads = await advertising_service.get_ads_for_platform(platform, user)
        
        # Inject ads if user is on free tier
        if user_plan.has_ads:
            videos = advertising_service.inject_ads_into_videos(videos, ads, user)
        
        # Store videos in database for analytics
        for video in videos:
            try:
                if not video.is_sponsored:  # Don't store ads as viral videos
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
            date=datetime.utcnow(),
            has_ads=user_plan.has_ads,
            user_tier=user.subscription_tier if user else SubscriptionTier.FREE
        )
    except Exception as e:
        logger.error(f"Error fetching videos: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching viral videos")

# User Management Routes
@api_router.post("/users/register", response_model=User)
async def register_user(user_data: UserCreate):
    """Register a new user"""
    try:
        user = await auth_service.create_user(user_data.email, user_data.name)
        return user
    except Exception as e:
        logger.error(f"Error registering user: {str(e)}")
        raise HTTPException(status_code=500, detail="Error registering user")

@api_router.get("/users/me", response_model=User)
async def get_current_user_info(user: User = Depends(require_user)):
    """Get current user information"""
    return user

@api_router.get("/users/me/analytics")
async def get_user_analytics(user: User = Depends(require_user)):
    """Get user analytics"""
    try:
        analytics = await auth_service.get_user_analytics(user.id)
        return analytics
    except Exception as e:
        logger.error(f"Error fetching user analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching analytics")

# Subscription Management Routes
@api_router.get("/subscription/plans")
async def get_subscription_plans():
    """Get all available subscription plans"""
    plans_data = []
    for tier, plan in SUBSCRIPTION_PLANS.items():
        plan_dict = plan.dict()
        plan_dict["savings_percentage"] = round(((plan.price_monthly * 12 - plan.price_yearly) / (plan.price_monthly * 12) * 100), 1) if plan.price_monthly > 0 else 0
        plans_data.append(plan_dict)
    
    return {"plans": plans_data}

@api_router.get("/subscription/me")
async def get_my_subscription(user: User = Depends(require_user)):
    """Get current user's subscription details"""
    plan = get_plan(user.subscription_tier)
    return {
        "user_id": user.id,
        "current_tier": user.subscription_tier,
        "plan_details": plan.dict(),
        "expires_at": user.subscription_expires_at,
        "api_usage_today": user.daily_api_calls,
        "api_limit": user.max_daily_api_calls
    }

# Legacy subscription route (for backward compatibility)
@api_router.post("/subscribe", response_model=OldSubscription)
async def create_legacy_subscription(subscription_data: SubscriptionCreate):
    """Create a legacy subscription for daily viral video delivery"""
    try:
        subscription = OldSubscription(**subscription_data.dict())
        await db.subscriptions.insert_one(subscription.dict())
        return subscription
    except Exception as e:
        logger.error(f"Error creating subscription: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating subscription")

# Analytics Routes (Business Tier)
@api_router.get("/analytics/dashboard")
async def get_analytics_dashboard(user: User = Depends(require_business_user)):
    """Get comprehensive analytics dashboard"""
    try:
        dashboard_data = await analytics_service.create_analytics_dashboard_data(user.id)
        return dashboard_data
    except Exception as e:
        logger.error(f"Error fetching dashboard data: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching analytics")

@api_router.get("/analytics/platforms")
async def get_platform_analytics(
    platform: Optional[Platform] = None,
    days: int = 30,
    user: User = Depends(require_pro_user)
):
    """Get platform-specific analytics"""
    try:
        analytics = await analytics_service.get_platform_analytics(platform, days)
        return analytics
    except Exception as e:
        logger.error(f"Error fetching platform analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching platform analytics")

# Include routers
app.include_router(api_router)
app.include_router(payments_router)
app.include_router(paypal_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize sample data and services"""
    try:
        # Create sample advertisements
        await advertising_service.create_sample_ads()
        logger.info("Startup completed successfully")
    except Exception as e:
        logger.error(f"Error during startup: {e}")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()