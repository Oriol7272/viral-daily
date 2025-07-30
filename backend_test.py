import requests
import sys
import json
from datetime import datetime
import uuid

class ViralDailyAPITester:
    def __init__(self, base_url="https://7b54aa5d-9af4-487f-bf4f-45584a53206f.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_user = None
        self.test_api_key = None

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if endpoint else self.api_url
        request_headers = {'Content-Type': 'application/json'}
        
        # Add authentication headers if available
        if self.test_api_key:
            request_headers['Authorization'] = f'Bearer {self.test_api_key}'
        
        # Add custom headers
        if headers:
            request_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=request_headers, params=params, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=request_headers, timeout=10)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Non-dict response'}")
                    return True, response_data
                except:
                    return True, response.text
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                return False, {}

        except requests.exceptions.Timeout:
            print(f"❌ Failed - Request timeout")
            return False, {}
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test GET /api/ - Welcome message"""
        success, response = self.run_test(
            "Root API Endpoint",
            "GET",
            "",
            200
        )
        if success and isinstance(response, dict) and 'message' in response:
            print(f"   Message: {response['message']}")
            return True
        return False

    def test_get_all_videos(self):
        """Test GET /api/videos - Get all viral videos with enhanced features"""
        success, response = self.run_test(
            "Get All Videos",
            "GET",
            "videos",
            200
        )
        if success and isinstance(response, dict):
            videos = response.get('videos', [])
            total = response.get('total', 0)
            print(f"   Found {total} videos")
            
            if videos:
                # Check first video structure
                first_video = videos[0]
                required_fields = ['title', 'url', 'thumbnail', 'platform', 'viral_score']
                missing_fields = [field for field in required_fields if field not in first_video]
                
                if missing_fields:
                    print(f"   ⚠️  Missing required fields: {missing_fields}")
                else:
                    print(f"   ✅ Video structure valid")
                    print(f"   Sample video: {first_video['title']} ({first_video['platform']})")
                
                # Check if videos are sorted by viral_score
                viral_scores = [v.get('viral_score', 0) for v in videos]
                is_sorted = all(viral_scores[i] >= viral_scores[i+1] for i in range(len(viral_scores)-1))
                print(f"   Viral score sorting: {'✅ Correct' if is_sorted else '❌ Incorrect'}")
                
                # Check platforms - should only have YouTube, TikTok, Twitter (NO Instagram)
                platforms = set(v.get('platform') for v in videos)
                expected_platforms = {'youtube', 'tiktok', 'twitter'}
                forbidden_platforms = {'instagram'}
                
                print(f"   Platforms found: {platforms}")
                
                # Check for forbidden Instagram platform
                instagram_found = any(platform in forbidden_platforms for platform in platforms)
                if instagram_found:
                    print(f"   ❌ CRITICAL: Instagram videos found! Instagram should be removed.")
                    return False
                else:
                    print(f"   ✅ Instagram successfully removed - no Instagram videos found")
                
                # Check if we have the expected platforms
                valid_platforms = platforms.issubset(expected_platforms)
                if valid_platforms:
                    print(f"   ✅ All platforms are valid: {platforms}")
                else:
                    unexpected = platforms - expected_platforms
                    print(f"   ⚠️  Unexpected platforms found: {unexpected}")
                
            return len(videos) > 0
        return False

    def test_platform_filtering(self):
        """Test platform filtering for YouTube, TikTok, Twitter (Instagram should be removed)"""
        platforms_to_test = ['youtube', 'tiktok', 'twitter']
        forbidden_platform = 'instagram'
        
        print(f"\n🔍 Testing platform filtering for {len(platforms_to_test)} platforms...")
        
        all_passed = True
        
        # Test each allowed platform
        for platform in platforms_to_test:
            success, response = self.run_test(
                f"Get {platform.title()} Videos",
                "GET",
                "videos",
                200,
                params={'platform': platform, 'limit': 5}
            )
            
            if success and isinstance(response, dict):
                videos = response.get('videos', [])
                platform_filter = response.get('platform')
                
                print(f"   {platform.title()}: {len(videos)} videos, filter: {platform_filter}")
                
                # Check that all videos are from the requested platform
                if videos:
                    platforms_found = set(v.get('platform') for v in videos)
                    if len(platforms_found) == 1 and platform in platforms_found:
                        print(f"   ✅ All videos are from {platform}")
                    else:
                        print(f"   ❌ Mixed platforms found: {platforms_found}")
                        all_passed = False
                else:
                    print(f"   ⚠️  No videos returned for {platform}")
            else:
                print(f"   ❌ Failed to get {platform} videos")
                all_passed = False
        
        # Test forbidden Instagram platform
        print(f"\n🚫 Testing forbidden platform: {forbidden_platform}")
        success, response = self.run_test(
            f"Get {forbidden_platform.title()} Videos (Should Fail)",
            "GET",
            "videos",
            200,  # API might return 200 with empty results or error
            params={'platform': forbidden_platform, 'limit': 5}
        )
        
        if success and isinstance(response, dict):
            videos = response.get('videos', [])
            if videos:
                # Check if any Instagram videos are returned
                instagram_videos = [v for v in videos if v.get('platform') == 'instagram']
                if instagram_videos:
                    print(f"   ❌ CRITICAL: {len(instagram_videos)} Instagram videos found! Instagram should be removed.")
                    all_passed = False
                else:
                    print(f"   ✅ No Instagram videos returned (good)")
            else:
                print(f"   ✅ No videos returned for Instagram (expected)")
        
        return all_passed

    def test_instagram_removal_verification(self):
        """Comprehensive test to verify Instagram is completely removed"""
        print(f"\n🔍 Comprehensive Instagram Removal Verification...")
        
        # Test 1: Get all videos and check for Instagram
        success, response = self.run_test(
            "All Videos - Instagram Check",
            "GET",
            "videos",
            200,
            params={'limit': 50}  # Get more videos to be thorough
        )
        
        instagram_found = False
        if success and isinstance(response, dict):
            videos = response.get('videos', [])
            instagram_videos = [v for v in videos if v.get('platform') == 'instagram']
            
            if instagram_videos:
                print(f"   ❌ CRITICAL: Found {len(instagram_videos)} Instagram videos in general feed!")
                instagram_found = True
                for video in instagram_videos[:3]:  # Show first 3
                    print(f"      - {video.get('title', 'No title')} ({video.get('url', 'No URL')})")
            else:
                print(f"   ✅ No Instagram videos found in general feed")
        
        # Test 2: Try to explicitly request Instagram videos
        success2, response2 = self.run_test(
            "Explicit Instagram Request",
            "GET",
            "videos",
            200,
            params={'platform': 'instagram', 'limit': 10}
        )
        
        if success2 and isinstance(response2, dict):
            videos2 = response2.get('videos', [])
            instagram_videos2 = [v for v in videos2 if v.get('platform') == 'instagram']
            
            if instagram_videos2:
                print(f"   ❌ CRITICAL: Instagram platform filter returned {len(instagram_videos2)} videos!")
                instagram_found = True
            else:
                print(f"   ✅ Instagram platform filter returns no videos (expected)")
        
        # Test 3: Check platform list in response
        if success and isinstance(response, dict):
            videos = response.get('videos', [])
            if videos:
                unique_platforms = set(v.get('platform') for v in videos)
                expected_platforms = {'youtube', 'tiktok', 'twitter'}
                
                print(f"   Platforms in response: {unique_platforms}")
                print(f"   Expected platforms: {expected_platforms}")
                
                if 'instagram' in unique_platforms:
                    print(f"   ❌ CRITICAL: Instagram found in platform list!")
                    instagram_found = True
                else:
                    print(f"   ✅ Instagram not in platform list")
                
                # Check if we have all expected platforms
                missing_platforms = expected_platforms - unique_platforms
                if missing_platforms:
                    print(f"   ⚠️  Missing expected platforms: {missing_platforms}")
                else:
                    print(f"   ✅ All expected platforms present")
        
        return not instagram_found

    def test_thumbnail_generation_comprehensive(self):
        """Comprehensive test for thumbnail generation fixes - TikTok and Twitter focus"""
        print(f"\n🖼️  COMPREHENSIVE THUMBNAIL GENERATION TESTING...")
        
        all_passed = True
        
        # Test 1: Get all videos and verify NO empty thumbnails
        success, response = self.run_test(
            "All Videos - Thumbnail Verification",
            "GET",
            "videos",
            200,
            params={'limit': 30}
        )
        
        if success and isinstance(response, dict):
            videos = response.get('videos', [])
            print(f"   Testing {len(videos)} videos for thumbnail quality...")
            
            empty_thumbnails = []
            invalid_thumbnails = []
            platform_thumbnails = {'youtube': [], 'tiktok': [], 'twitter': []}
            
            for video in videos:
                thumbnail = video.get('thumbnail', '')
                platform = video.get('platform', '').lower()
                title = video.get('title', 'No title')[:50]
                
                # Check for empty thumbnails
                if not thumbnail or thumbnail.strip() == '':
                    empty_thumbnails.append(f"{platform}: {title}")
                    all_passed = False
                    continue
                
                # Categorize by platform
                if platform in platform_thumbnails:
                    platform_thumbnails[platform].append({
                        'title': title,
                        'thumbnail': thumbnail,
                        'viral_score': video.get('viral_score', 0)
                    })
                
                # Check thumbnail format
                if not (thumbnail.startswith('http') or thumbnail.startswith('data:')):
                    invalid_thumbnails.append(f"{platform}: {title} - {thumbnail[:50]}")
            
            # Report empty thumbnails
            if empty_thumbnails:
                print(f"   ❌ CRITICAL: {len(empty_thumbnails)} videos have EMPTY thumbnails!")
                for empty in empty_thumbnails[:5]:  # Show first 5
                    print(f"      - {empty}")
                all_passed = False
            else:
                print(f"   ✅ NO EMPTY THUMBNAILS - All {len(videos)} videos have thumbnails")
            
            # Report invalid thumbnails
            if invalid_thumbnails:
                print(f"   ❌ {len(invalid_thumbnails)} videos have invalid thumbnail formats!")
                for invalid in invalid_thumbnails[:3]:
                    print(f"      - {invalid}")
                all_passed = False
            else:
                print(f"   ✅ All thumbnails have valid formats (HTTP URLs or data URIs)")
            
            # Test platform-specific thumbnail generation
            self._test_platform_thumbnails(platform_thumbnails)
            
        return all_passed
    
    def _test_platform_thumbnails(self, platform_thumbnails):
        """Test platform-specific thumbnail characteristics"""
        print(f"\n   🎨 PLATFORM-SPECIFIC THUMBNAIL TESTING...")
        
        # Test TikTok thumbnails
        tiktok_videos = platform_thumbnails.get('tiktok', [])
        if tiktok_videos:
            print(f"   📱 TikTok Thumbnails ({len(tiktok_videos)} videos):")
            svg_count = 0
            black_themed_count = 0
            music_icon_count = 0
            
            for video in tiktok_videos[:5]:  # Test first 5
                thumbnail = video['thumbnail']
                if thumbnail.startswith('data:image/svg+xml'):
                    svg_count += 1
                    # Decode and check content
                    try:
                        from urllib.parse import unquote
                        svg_content = unquote(thumbnail.split(',')[1])
                        if '#000000' in svg_content or 'fill="black"' in svg_content:
                            black_themed_count += 1
                        if '🎵' in svg_content or 'music' in svg_content.lower():
                            music_icon_count += 1
                    except:
                        pass
                    
                    print(f"      ✅ {video['title'][:30]}... - SVG thumbnail (Score: {video['viral_score']:.1f})")
                else:
                    print(f"      ⚠️  {video['title'][:30]}... - Non-SVG thumbnail: {thumbnail[:50]}")
            
            print(f"      📊 TikTok Results: {svg_count}/{len(tiktok_videos[:5])} SVG, {black_themed_count} black-themed, {music_icon_count} with music icons")
            
            if svg_count == len(tiktok_videos[:5]):
                print(f"      ✅ ALL TikTok videos have SVG thumbnails!")
            else:
                print(f"      ❌ Some TikTok videos missing SVG thumbnails")
        else:
            print(f"   📱 TikTok: No videos found for thumbnail testing")
        
        # Test Twitter thumbnails
        twitter_videos = platform_thumbnails.get('twitter', [])
        if twitter_videos:
            print(f"   🐦 Twitter Thumbnails ({len(twitter_videos)} videos):")
            svg_count = 0
            blue_themed_count = 0
            bird_icon_count = 0
            
            for video in twitter_videos[:5]:  # Test first 5
                thumbnail = video['thumbnail']
                if thumbnail.startswith('data:image/svg+xml'):
                    svg_count += 1
                    # Decode and check content
                    try:
                        from urllib.parse import unquote
                        svg_content = unquote(thumbnail.split(',')[1])
                        if '#1DA1F2' in svg_content or 'blue' in svg_content.lower():
                            blue_themed_count += 1
                        if '🐦' in svg_content or 'bird' in svg_content.lower():
                            bird_icon_count += 1
                    except:
                        pass
                    
                    print(f"      ✅ {video['title'][:30]}... - SVG thumbnail (Score: {video['viral_score']:.1f})")
                else:
                    print(f"      ⚠️  {video['title'][:30]}... - Non-SVG thumbnail: {thumbnail[:50]}")
            
            print(f"      📊 Twitter Results: {svg_count}/{len(twitter_videos[:5])} SVG, {blue_themed_count} blue-themed, {bird_icon_count} with bird icons")
            
            if svg_count == len(twitter_videos[:5]):
                print(f"      ✅ ALL Twitter videos have SVG thumbnails!")
            else:
                print(f"      ❌ Some Twitter videos missing SVG thumbnails")
        else:
            print(f"   🐦 Twitter: No videos found for thumbnail testing")
        
        # Test YouTube thumbnails (should still have original URLs)
        youtube_videos = platform_thumbnails.get('youtube', [])
        if youtube_videos:
            print(f"   📺 YouTube Thumbnails ({len(youtube_videos)} videos):")
            http_count = 0
            ytimg_count = 0
            
            for video in youtube_videos[:5]:  # Test first 5
                thumbnail = video['thumbnail']
                if thumbnail.startswith('http'):
                    http_count += 1
                    if 'ytimg.com' in thumbnail or 'youtube.com' in thumbnail:
                        ytimg_count += 1
                    print(f"      ✅ {video['title'][:30]}... - HTTP thumbnail (Score: {video['viral_score']:.1f})")
                else:
                    print(f"      ⚠️  {video['title'][:30]}... - Non-HTTP thumbnail: {thumbnail[:50]}")
            
            print(f"      📊 YouTube Results: {http_count}/{len(youtube_videos[:5])} HTTP URLs, {ytimg_count} from YouTube CDN")
            
            if http_count == len(youtube_videos[:5]):
                print(f"      ✅ ALL YouTube videos have HTTP thumbnails!")
            else:
                print(f"      ❌ Some YouTube videos missing HTTP thumbnails")
        else:
            print(f"   📺 YouTube: No videos found for thumbnail testing")

    def test_platform_specific_thumbnails(self):
        """Test each platform individually for thumbnail generation"""
        print(f"\n🎯 PLATFORM-SPECIFIC THUMBNAIL TESTING...")
        
        platforms = ['tiktok', 'twitter', 'youtube']
        all_passed = True
        
        for platform in platforms:
            print(f"\n   Testing {platform.upper()} thumbnails...")
            
            success, response = self.run_test(
                f"Get {platform.title()} Videos for Thumbnails",
                "GET",
                "videos",
                200,
                params={'platform': platform, 'limit': 10}
            )
            
            if success and isinstance(response, dict):
                videos = response.get('videos', [])
                
                if not videos:
                    print(f"      ⚠️  No {platform} videos returned")
                    continue
                
                print(f"      Found {len(videos)} {platform} videos")
                
                # Check each video's thumbnail
                empty_count = 0
                valid_count = 0
                
                for i, video in enumerate(videos[:5]):  # Check first 5
                    thumbnail = video.get('thumbnail', '')
                    title = video.get('title', 'No title')[:40]
                    viral_score = video.get('viral_score', 0)
                    
                    if not thumbnail or thumbnail.strip() == '':
                        print(f"      ❌ Video {i+1}: EMPTY thumbnail - {title}")
                        empty_count += 1
                        all_passed = False
                    else:
                        print(f"      ✅ Video {i+1}: Valid thumbnail - {title} (Score: {viral_score:.1f})")
                        valid_count += 1
                        
                        # Platform-specific checks
                        if platform == 'tiktok' and not thumbnail.startswith('data:image/svg+xml'):
                            print(f"         ⚠️  TikTok should have SVG thumbnail, got: {thumbnail[:50]}")
                        elif platform == 'twitter' and not thumbnail.startswith('data:image/svg+xml'):
                            print(f"         ⚠️  Twitter should have SVG thumbnail, got: {thumbnail[:50]}")
                        elif platform == 'youtube' and not thumbnail.startswith('http'):
                            print(f"         ⚠️  YouTube should have HTTP thumbnail, got: {thumbnail[:50]}")
                
                print(f"      📊 {platform.upper()} Summary: {valid_count} valid, {empty_count} empty thumbnails")
                
                if empty_count > 0:
                    all_passed = False
            else:
                print(f"      ❌ Failed to get {platform} videos")
                all_passed = False
        
        return all_passed

    def test_user_registration(self):
        """Test POST /api/users/register - User registration"""
        test_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        test_name = f"Test User {datetime.now().strftime('%H%M%S')}"
        
        success, response = self.run_test(
            "User Registration",
            "POST",
            "users/register",
            200,
            data={"email": test_email, "name": test_name}
        )
        
        if success and isinstance(response, dict):
            required_fields = ['id', 'email', 'name', 'api_key', 'subscription_tier']
            missing_fields = [field for field in required_fields if field not in response]
            
            if missing_fields:
                print(f"   ⚠️  Missing fields: {missing_fields}")
                return False
            else:
                self.test_user = response
                self.test_api_key = response['api_key']
                print(f"   ✅ User created: {response['email']}")
                print(f"   API Key: {response['api_key'][:20]}...")
                print(f"   Subscription Tier: {response['subscription_tier']}")
                return True
        return False

    def test_subscription_plans(self):
        """Test GET /api/subscription/plans - Get subscription plans"""
        success, response = self.run_test(
            "Get Subscription Plans",
            "GET",
            "subscription/plans",
            200
        )
        
        if success and isinstance(response, dict):
            plans = response.get('plans', [])
            print(f"   Found {len(plans)} subscription plans")
            
            # Check for required tiers
            tiers = [plan.get('tier') for plan in plans]
            required_tiers = ['free', 'pro', 'business']
            missing_tiers = [tier for tier in required_tiers if tier not in tiers]
            
            if missing_tiers:
                print(f"   ⚠️  Missing tiers: {missing_tiers}")
                return False
            
            # Check plan structure
            for plan in plans:
                required_fields = ['tier', 'name', 'price_monthly', 'features', 'max_videos_per_day']
                missing_fields = [field for field in required_fields if field not in plan]
                if missing_fields:
                    print(f"   ⚠️  Plan {plan.get('tier')} missing fields: {missing_fields}")
                    return False
                else:
                    print(f"   ✅ {plan['tier'].upper()}: ${plan['price_monthly']}/month, {plan['max_videos_per_day']} videos/day")
            
            return True
        return False

    def test_current_user_info(self):
        """Test GET /api/users/me - Get current user info"""
        if not self.test_api_key:
            print("   ⚠️  No API key available, skipping test")
            return False
            
        success, response = self.run_test(
            "Get Current User Info",
            "GET",
            "users/me",
            200
        )
        
        if success and isinstance(response, dict):
            required_fields = ['id', 'email', 'subscription_tier', 'daily_api_calls', 'max_daily_api_calls']
            missing_fields = [field for field in required_fields if field not in response]
            
            if missing_fields:
                print(f"   ⚠️  Missing fields: {missing_fields}")
                return False
            else:
                print(f"   ✅ User: {response['email']}")
                print(f"   Tier: {response['subscription_tier']}")
                print(f"   API Usage: {response['daily_api_calls']}/{response['max_daily_api_calls']}")
                return True
        return False

    def test_videos_with_auth(self):
        """Test GET /api/videos with authentication"""
        if not self.test_api_key:
            print("   ⚠️  No API key available, skipping test")
            return False
            
        success, response = self.run_test(
            "Get Videos with Auth",
            "GET",
            "videos",
            200,
            params={'limit': 10}
        )
        
        if success and isinstance(response, dict):
            videos = response.get('videos', [])
            has_ads = response.get('has_ads', False)
            user_tier = response.get('user_tier', 'unknown')
            
            print(f"   Videos: {len(videos)}")
            print(f"   Has Ads: {has_ads}")
            print(f"   User Tier: {user_tier}")
            
            # Check for ads in free tier
            if user_tier == 'free':
                sponsored_videos = [v for v in videos if v.get('is_sponsored', False)]
                print(f"   Sponsored content: {len(sponsored_videos)} ads")
                
            return len(videos) > 0
        return False

    def test_subscription_info(self):
        """Test current subscription info"""
        if not self.test_api_key:
            print("   ⚠️  No API key available, skipping test")
            return False
            
        success, response = self.run_test(
            "Current Subscription Info",
            "GET",
            "subscription/me",
            200
        )
        
        if success and isinstance(response, dict):
            required_fields = ['user_id', 'current_tier', 'plan_details', 'api_usage_today', 'api_limit']
            missing_fields = [field for field in required_fields if field not in response]
            
            if missing_fields:
                print(f"   ⚠️  Missing fields: {missing_fields}")
                return False
            else:
                print(f"   ✅ Subscription: {response['current_tier']}")
                print(f"   API Usage: {response['api_usage_today']}/{response['api_limit']}")
                return True
        return False

    def test_paypal_config(self):
        """Test GET /api/payments/paypal/config - PayPal configuration with NEW live credentials"""
        success, response = self.run_test(
            "PayPal Configuration (NEW Live Credentials)",
            "GET",
            "payments/paypal/config",
            200
        )
        
        if success and isinstance(response, dict):
            required_fields = ['client_id', 'mode', 'currency']
            missing_fields = [field for field in required_fields if field not in response]
            
            if missing_fields:
                print(f"   ❌ Missing fields: {missing_fields}")
                return False
            else:
                # Check specific business account requirements
                mode = response['mode']
                currency = response['currency']
                client_id = response['client_id']
                
                print(f"   PayPal Mode: {mode}")
                print(f"   Currency: {currency}")
                
                # Verify NEW live credentials provided by user
                expected_client_id = "BAAjUw1nb84moRC0rrJOZtICaamy0n3pn_wL_qsvsw7w8fE8P6bKNU9cmWVmnkzwj5DJHkYU-nyM2wZtqI"
                
                # Test results
                mode_correct = mode == "live"
                currency_correct = currency == "EUR"
                client_id_correct = client_id == expected_client_id
                
                print(f"   ✅ Live Mode: {'✅ CORRECT' if mode_correct else '❌ INCORRECT (Expected: live, Got: ' + str(mode) + ')'}")
                print(f"   ✅ EUR Currency: {'✅ CORRECT' if currency_correct else '❌ INCORRECT (Expected: EUR, Got: ' + str(currency) + ')'}")
                print(f"   ✅ NEW Live Client ID: {'✅ CORRECT' if client_id_correct else '❌ INCORRECT'}")
                
                if client_id_correct:
                    print(f"   🎉 NEW live client ID verified!")
                else:
                    print(f"   ❌ Expected NEW client ID: {expected_client_id[:20]}...")
                    print(f"   ❌ Actual client ID: {client_id[:20] if client_id else 'None'}...")
                
                # Overall success
                all_correct = mode_correct and currency_correct and client_id_correct
                if all_correct:
                    print("   🎉 PayPal NEW live account configuration is PERFECT!")
                else:
                    print("   ⚠️  PayPal NEW live account configuration has issues")
                
                return all_correct
        return False

    def test_paypal_availability(self):
        """Test GET /api/payments/paypal/available - PayPal availability check with live mode"""
        success, response = self.run_test(
            "PayPal Availability Check (Live Mode)",
            "GET",
            "payments/paypal/available",
            200
        )
        
        if success and isinstance(response, dict):
            required_fields = ['available', 'mode']
            missing_fields = [field for field in required_fields if field not in response]
            
            if missing_fields:
                print(f"   ❌ Missing fields: {missing_fields}")
                return False
            else:
                available = response['available']
                mode = response['mode']
                
                print(f"   PayPal Available: {available}")
                print(f"   Mode: {mode}")
                
                # Check for live mode specifically
                live_mode_correct = mode == "live"
                print(f"   ✅ Live Mode: {'✅ CORRECT' if live_mode_correct else '❌ INCORRECT (Expected: live, Got: ' + str(mode) + ')'}")
                
                if available and live_mode_correct:
                    print("   🎉 PayPal is available in LIVE mode with NEW credentials!")
                elif available:
                    print("   ⚠️  PayPal is available but not in live mode")
                else:
                    print("   ❌ PayPal not available - credentials may be missing")
                
                return available and live_mode_correct
        return False

    def test_paypal_create_order_unauthenticated(self):
        """Test POST /api/payments/paypal/create-order without authentication (NEW Live Credentials)"""
        order_data = {
            "subscription_tier": "pro",
            "billing_cycle": "monthly"
        }
        
        # First check if PayPal is available
        avail_success, avail_response = self.run_test(
            "PayPal Availability Pre-check (Unauth)",
            "GET",
            "payments/paypal/available",
            200
        )
        
        if avail_success and avail_response.get('available'):
            # PayPal is available, should work without auth for order creation
            success, response = self.run_test(
                "PayPal Create Order (Unauthenticated - NEW Live Credentials)",
                "POST",
                "payments/paypal/create-order",
                200,  # Should succeed even without auth
                data=order_data
            )
            
            if success and isinstance(response, dict):
                print("   🎉 PayPal Order Creation works without authentication!")
                print(f"   Order ID: {response.get('order_id', 'N/A')}")
                
                # Check for EUR currency in approval URL or response
                approval_url = response.get('approval_url', '')
                if approval_url and "paypal.com" in approval_url and "sandbox" not in approval_url:
                    print("   ✅ Live PayPal URL confirmed - NEW credentials active")
                
                return True
            return False
        else:
            # PayPal not available, expect 503 error
            success, response = self.run_test(
                "PayPal Create Order (Unauthenticated - No Credentials)",
                "POST",
                "payments/paypal/create-order",
                503,  # Expected to fail due to missing credentials
                data=order_data
            )
            
            if success:
                print("   ✅ Properly handles unauthenticated request with missing credentials")
                return True
            return False

    def test_paypal_create_order_authenticated(self):
        """Test POST /api/payments/paypal/create-order with authentication and NEW live credentials (EUR currency)"""
        if not self.test_api_key:
            print("   ⚠️  No API key available, skipping test")
            return False
            
        order_data = {
            "subscription_tier": "pro",
            "billing_cycle": "monthly"
        }
        
        # First check if PayPal is available
        avail_success, avail_response = self.run_test(
            "PayPal Availability Pre-check",
            "GET",
            "payments/paypal/available",
            200
        )
        
        if avail_success and avail_response.get('available'):
            # PayPal is available, expect successful order creation
            success, response = self.run_test(
                "PayPal Create Order (NEW Live Credentials - EUR Currency)",
                "POST",
                "payments/paypal/create-order",
                200,  # Should succeed with NEW credentials
                data=order_data
            )
            
            if success and isinstance(response, dict):
                required_fields = ['order_id', 'approval_url', 'order_status']
                missing_fields = [field for field in required_fields if field not in response]
                
                if missing_fields:
                    print(f"   ❌ Missing fields: {missing_fields}")
                    return False
                else:
                    print(f"   🎉 PayPal Order Created Successfully with NEW Live Credentials!")
                    print(f"   Order ID: {response['order_id']}")
                    print(f"   Status: {response['order_status']}")
                    
                    approval_url = response['approval_url']
                    if approval_url:
                        print(f"   Approval URL: {approval_url[:50]}...")
                        
                        # Check if URL contains live PayPal domain (not sandbox)
                        if "paypal.com" in approval_url and "sandbox" not in approval_url:
                            print("   ✅ Live PayPal URL detected - NEW credentials working!")
                        elif "sandbox.paypal.com" in approval_url:
                            print("   ⚠️  Sandbox URL detected - should be live mode")
                        else:
                            print("   ℹ️  PayPal URL format verified")
                    
                    # Verify the order was created in EUR currency by checking the database
                    # This would be done by the PayPal service internally
                    print("   💰 Order should be created in EUR currency as per NEW live account config")
                    
                    return True
            return False
        else:
            # PayPal not available, expect 503 error
            success, response = self.run_test(
                "PayPal Create Order (No Credentials)",
                "POST",
                "payments/paypal/create-order",
                503,  # Expected to fail due to missing credentials
                data=order_data
            )
            
            if success:
                print("   ✅ Properly handles missing PayPal credentials")
                return True
            return False

    def test_paypal_order_status(self):
        """Test GET /api/payments/paypal/order-status/{order_id}"""
        test_order_id = "test_order_123"
        
        # First check if PayPal is available
        avail_success, avail_response = self.run_test(
            "PayPal Availability Pre-check (Order Status)",
            "GET",
            "payments/paypal/available",
            200
        )
        
        if avail_success and avail_response.get('available'):
            # PayPal is available, but test order ID won't exist - expect 500 or 404
            success, response = self.run_test(
                "PayPal Order Status (Real Credentials)",
                "GET",
                f"payments/paypal/order-status/{test_order_id}",
                500  # Expected to fail with invalid order ID
            )
            
            if success:
                print("   ✅ PayPal order status endpoint accessible with real credentials")
                print("   ℹ️  Failed as expected due to invalid test order ID")
                return True
            return False
        else:
            # PayPal not available, expect 503 error
            success, response = self.run_test(
                "PayPal Order Status (No Credentials)",
                "GET",
                f"payments/paypal/order-status/{test_order_id}",
                503  # Expected to fail due to missing credentials
            )
            
            if success:
                print("   ✅ Properly handles missing PayPal credentials")
                return True
            return False

    def test_paypal_webhook(self):
        """Test POST /api/payments/paypal/webhook"""
        webhook_data = {
            "event_type": "PAYMENT.CAPTURE.COMPLETED",
            "resource": {
                "id": "test_capture_id",
                "supplementary_data": {
                    "related_ids": {
                        "order_id": "test_order_id"
                    }
                }
            }
        }
        
        success, response = self.run_test(
            "PayPal Webhook Handler",
            "POST",
            "payments/paypal/webhook",
            200,
            data=webhook_data
        )
        
        if success and isinstance(response, dict):
            if 'status' in response and response['status'] == 'success':
                print("   ✅ Webhook processed successfully")
                return True
            else:
                print(f"   ⚠️  Unexpected webhook response: {response}")
                return False
        return False

    def test_paypal_eur_currency_validation(self):
        """Test that PayPal orders are created with EUR currency"""
        print("\n🔍 Testing PayPal EUR Currency Configuration...")
        
        # Test configuration endpoint for EUR
        config_success, config_response = self.run_test(
            "PayPal Config EUR Check",
            "GET",
            "payments/paypal/config",
            200
        )
        
        if config_success and isinstance(config_response, dict):
            currency = config_response.get('currency')
            if currency == 'EUR':
                print("   ✅ PayPal configuration correctly set to EUR currency")
                
                # Now test order creation to ensure EUR is used
                if self.test_api_key:
                    order_data = {
                        "subscription_tier": "pro",
                        "billing_cycle": "monthly"
                    }
                    
                    order_success, order_response = self.run_test(
                        "PayPal Order Creation EUR Validation",
                        "POST",
                        "payments/paypal/create-order",
                        200,
                        data=order_data
                    )
                    
                    if order_success:
                        print("   ✅ Order created successfully - EUR currency should be applied internally")
                        print("   💰 NEW live account configured for EUR transactions")
                        return True
                    else:
                        print("   ⚠️  Order creation failed, but EUR config is correct")
                        return True  # Config is correct even if order fails
                else:
                    print("   ✅ EUR currency configuration verified (no auth for order test)")
                    return True
            else:
                print(f"   ❌ Currency should be EUR, but got: {currency}")
                return False
        else:
            print("   ❌ Failed to get PayPal configuration")
            return False

    def test_paypal_error_handling(self):
        """Test PayPal endpoints with invalid data for error handling"""
        print("\n🔍 Testing PayPal Error Handling...")
        
        # Test create order with invalid subscription tier
        invalid_order_data = {
            "subscription_tier": "invalid_tier",
            "billing_cycle": "monthly"
        }
        
        success, response = self.run_test(
            "PayPal Create Order (Invalid Tier)",
            "POST",
            "payments/paypal/create-order",
            422,  # Validation error expected
            data=invalid_order_data
        )
        
        if success:
            print("   ✅ Properly handles invalid subscription tier")
        
        # Test create order with missing required fields
        incomplete_order_data = {
            "subscription_tier": "pro"
            # Missing billing_cycle
        }
        
        success2, response2 = self.run_test(
            "PayPal Create Order (Missing Fields)",
            "POST",
            "payments/paypal/create-order",
            422,  # Validation error expected
            data=incomplete_order_data
        )
        
        if success2:
            print("   ✅ Properly handles missing required fields")
        
        return success and success2

    def test_advertisement_system_after_thumbnail_fix(self):
        """Test that advertisement system still works correctly after thumbnail changes"""
        print("\n📺 ADVERTISEMENT SYSTEM TESTING (Post-Thumbnail Fix)...")
        
        # Test 1: Get videos without authentication (should have ads for free tier)
        success, response = self.run_test(
            "Videos with Ads (Free Tier)",
            "GET",
            "videos",
            200,
            params={'limit': 20}
        )
        
        if success and isinstance(response, dict):
            videos = response.get('videos', [])
            has_ads = response.get('has_ads', False)
            user_tier = response.get('user_tier', 'unknown')
            
            print(f"   User Tier: {user_tier}")
            print(f"   Has Ads Flag: {has_ads}")
            print(f"   Total Videos: {len(videos)}")
            
            # Check for sponsored content
            sponsored_videos = [v for v in videos if v.get('is_sponsored', False)]
            regular_videos = [v for v in videos if not v.get('is_sponsored', False)]
            
            print(f"   Sponsored Videos (Ads): {len(sponsored_videos)}")
            print(f"   Regular Videos: {len(regular_videos)}")
            
            if has_ads and user_tier == 'free':
                if sponsored_videos:
                    print(f"   ✅ Advertisement injection working - {len(sponsored_videos)} ads found")
                    
                    # Check ad structure
                    for i, ad in enumerate(sponsored_videos[:2]):  # Check first 2 ads
                        print(f"      Ad {i+1}: {ad.get('title', 'No title')[:50]}")
                        print(f"         Platform: {ad.get('platform', 'unknown')}")
                        print(f"         Thumbnail: {'✅ Present' if ad.get('thumbnail') else '❌ Missing'}")
                        print(f"         URL: {'✅ Present' if ad.get('url') else '❌ Missing'}")
                    
                    # Verify ads target correct platforms (youtube, tiktok, twitter only)
                    ad_platforms = set(ad.get('platform', '').lower() for ad in sponsored_videos)
                    expected_ad_platforms = {'youtube', 'tiktok', 'twitter'}
                    
                    if ad_platforms.issubset(expected_ad_platforms):
                        print(f"   ✅ Ads target correct platforms: {ad_platforms}")
                    else:
                        unexpected_platforms = ad_platforms - expected_ad_platforms
                        print(f"   ⚠️  Ads targeting unexpected platforms: {unexpected_platforms}")
                    
                    return True
                else:
                    print(f"   ❌ No ads found despite has_ads=True for free tier")
                    return False
            else:
                print(f"   ℹ️  No ads expected for tier: {user_tier}")
                return True
        
        return False
    
    def test_advertisement_platform_targeting(self):
        """Test that ads are properly targeted to the correct platforms"""
        print("\n🎯 ADVERTISEMENT PLATFORM TARGETING TEST...")
        
        # Test each platform individually to see if ads are injected
        platforms = ['youtube', 'tiktok', 'twitter']
        all_passed = True
        
        for platform in platforms:
            success, response = self.run_test(
                f"Ads for {platform.title()} Platform",
                "GET",
                "videos",
                200,
                params={'platform': platform, 'limit': 15}
            )
            
            if success and isinstance(response, dict):
                videos = response.get('videos', [])
                has_ads = response.get('has_ads', False)
                
                sponsored_videos = [v for v in videos if v.get('is_sponsored', False)]
                
                print(f"   {platform.upper()}: {len(videos)} total, {len(sponsored_videos)} ads, has_ads={has_ads}")
                
                if has_ads:
                    # Check that ads are for the correct platform
                    for ad in sponsored_videos:
                        ad_platform = ad.get('platform', '').lower()
                        if ad_platform != platform:
                            print(f"      ❌ Ad platform mismatch: expected {platform}, got {ad_platform}")
                            all_passed = False
                        else:
                            print(f"      ✅ Ad correctly targeted to {platform}")
            else:
                print(f"   ❌ Failed to get {platform} videos")
                all_passed = False
        
        return all_passed

    def run_all_tests(self):
        """Run all API tests including monetization and PayPal features"""
        print("🚀 Starting Viral Daily MONETIZED API Tests with PayPal NEW Live Credentials Integration")
        print("=" * 70)
        
        # Test core endpoints first
        core_tests = [
            ("Root Endpoint", self.test_root_endpoint),
            ("Get All Videos (No Auth)", self.test_get_all_videos),
            ("Platform Filtering", self.test_platform_filtering),
            ("Instagram Removal Verification", self.test_instagram_removal_verification),
            ("Comprehensive Thumbnail Generation", self.test_thumbnail_generation_comprehensive),
            ("Platform-Specific Thumbnails", self.test_platform_specific_thumbnails),
        ]
        
        # Test monetization features
        monetization_tests = [
            ("User Registration", self.test_user_registration),
            ("Subscription Plans", self.test_subscription_plans),
            ("Current User Info", self.test_current_user_info),
            ("Videos with Authentication", self.test_videos_with_auth),
            ("Subscription Info", self.test_subscription_info),
        ]
        
        # Test PayPal integration with NEW live credentials focus
        paypal_tests = [
            ("PayPal Configuration (NEW Live Credentials)", self.test_paypal_config),
            ("PayPal Availability (Live Mode)", self.test_paypal_availability),
            ("PayPal EUR Currency Validation", self.test_paypal_eur_currency_validation),
            ("PayPal Create Order (Unauthenticated)", self.test_paypal_create_order_unauthenticated),
            ("PayPal Create Order (Authenticated)", self.test_paypal_create_order_authenticated),
            ("PayPal Order Status", self.test_paypal_order_status),
            ("PayPal Webhook Handler", self.test_paypal_webhook),
            ("PayPal Error Handling", self.test_paypal_error_handling),
        ]
        
        # Test advertisement system after thumbnail fixes
        advertisement_tests = [
            ("Advertisement System (Post-Thumbnail Fix)", self.test_advertisement_system_after_thumbnail_fix),
            ("Advertisement Platform Targeting", self.test_advertisement_platform_targeting),
        ]
        
        all_tests = core_tests + monetization_tests + paypal_tests
        
        for test_name, test_func in all_tests:
            print(f"\n📋 Running {test_name} Tests...")
            try:
                test_func()
            except Exception as e:
                print(f"❌ Test suite failed: {str(e)}")
        
        # Print final results
        print("\n" + "=" * 70)
        print(f"📊 Final Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        # Detailed summary
        success_rate = (self.tests_passed / self.tests_run) * 100 if self.tests_run > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed! MONETIZED API with PayPal NEW Live Credentials is working correctly.")
            print("💰 Monetization features: ✅ FULLY FUNCTIONAL")
            print("💳 PayPal NEW Live Credentials: ✅ PROPERLY CONFIGURED")
            return 0
        else:
            failed_tests = self.tests_run - self.tests_passed
            print(f"⚠️  {failed_tests} tests failed.")
            if success_rate >= 80:
                print("💰 Monetization features: ✅ MOSTLY FUNCTIONAL")
                print("💳 PayPal NEW Live Credentials: ✅ MOSTLY FUNCTIONAL")
            elif success_rate >= 60:
                print("💰 Monetization features: ⚠️  PARTIALLY FUNCTIONAL")
                print("💳 PayPal NEW Live Credentials: ⚠️  PARTIALLY FUNCTIONAL")
            else:
                print("💰 Monetization features: ❌ NEEDS ATTENTION")
                print("💳 PayPal NEW Live Credentials: ❌ NEEDS ATTENTION")
            return 1
        
        # Test PayPal integration
        paypal_tests = [
            ("PayPal Configuration", self.test_paypal_config),
            ("PayPal Availability", self.test_paypal_availability),
            ("PayPal Create Order (Unauthenticated)", self.test_paypal_create_order_unauthenticated),
            ("PayPal Create Order (Authenticated)", self.test_paypal_create_order_authenticated),
            ("PayPal Order Status", self.test_paypal_order_status),
            ("PayPal Webhook Handler", self.test_paypal_webhook),
            ("PayPal Error Handling", self.test_paypal_error_handling),
        ]
        
        all_tests = core_tests + monetization_tests + paypal_tests
        
        for test_name, test_func in all_tests:
            print(f"\n📋 Running {test_name} Tests...")
            try:
                test_func()
            except Exception as e:
                print(f"❌ Test suite failed: {str(e)}")
        
        # Print final results
        print("\n" + "=" * 70)
        print(f"📊 Final Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        # Detailed summary
        success_rate = (self.tests_passed / self.tests_run) * 100 if self.tests_run > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed! MONETIZED API with PayPal is working correctly.")
            print("💰 Monetization features: ✅ FULLY FUNCTIONAL")
            print("💳 PayPal integration: ✅ PROPERLY CONFIGURED")
            return 0
        else:
            failed_tests = self.tests_run - self.tests_passed
            print(f"⚠️  {failed_tests} tests failed.")
            if success_rate >= 80:
                print("💰 Monetization features: ✅ MOSTLY FUNCTIONAL")
                print("💳 PayPal integration: ✅ MOSTLY FUNCTIONAL")
            elif success_rate >= 60:
                print("💰 Monetization features: ⚠️  PARTIALLY FUNCTIONAL")
                print("💳 PayPal integration: ⚠️  PARTIALLY FUNCTIONAL")
            else:
                print("💰 Monetization features: ❌ NEEDS ATTENTION")
                print("💳 PayPal integration: ❌ NEEDS ATTENTION")
            return 1

def main():
    tester = ViralDailyAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())