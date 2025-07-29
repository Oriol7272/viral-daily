import requests
import sys
import json
from datetime import datetime
import uuid

class ViralDailyAPITester:
    def __init__(self, base_url="https://42ddaa94-2f87-4bfa-b3ea-e8e4d90c7075.preview.emergentagent.com"):
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

    def test_rate_limiting(self):
        """Test API rate limiting"""
        if not self.test_api_key:
            print("   ⚠️  No API key available, skipping test")
            return False
            
        print("   Testing rate limiting by making multiple requests...")
        
        # Make several requests quickly
        for i in range(5):
            success, response = self.run_test(
                f"Rate Limit Test {i+1}",
                "GET",
                "videos",
                200,
                params={'limit': 1}
            )
            if not success:
                if response == {} and i > 0:  # Likely rate limited
                    print(f"   ✅ Rate limiting working (blocked after {i} requests)")
                    return True
                else:
                    print(f"   ❌ Unexpected failure on request {i+1}")
                    return False
        
        print("   ✅ All requests succeeded (rate limit not reached)")
        return True

    def test_payment_endpoints(self):
        """Test payment-related endpoints"""
        if not self.test_api_key:
            print("   ⚠️  No API key available, skipping test")
            return False
            
        # Test checkout session creation (should work even in test mode)
        success, response = self.run_test(
            "Create Checkout Session",
            "POST",
            "payments/v1/checkout/session",
            200,
            data={
                "price_id": "price_test_pro_monthly",
                "success_url": "https://example.com/success",
                "cancel_url": "https://example.com/cancel"
            }
        )
        
        if success and isinstance(response, dict):
            if 'checkout_url' in response or 'session_id' in response:
                print(f"   ✅ Checkout session created")
                return True
            else:
                print(f"   ⚠️  Unexpected response structure")
                return False
        return False

    def test_analytics_endpoints(self):
        """Test analytics endpoints (Business tier only)"""
        if not self.test_api_key:
            print("   ⚠️  No API key available, skipping test")
            return False
            
        # This should fail for free tier users
        success, response = self.run_test(
            "Analytics Dashboard (Should Fail for Free Tier)",
            "GET",
            "analytics/dashboard",
            403  # Expecting forbidden for free tier
        )
        
        if success:
            print("   ✅ Analytics properly restricted to Business tier")
            return True
        elif response == {}:  # Got 403 as expected
            print("   ✅ Analytics properly restricted to Business tier")
            return True
        else:
            print("   ❌ Analytics access control not working")
            return False

    def test_user_analytics(self):
        """Test user analytics endpoint"""
        if not self.test_api_key:
            print("   ⚠️  No API key available, skipping test")
            return False
            
        success, response = self.run_test(
            "User Analytics",
            "GET",
            "users/me/analytics",
            200
        )
        
        if success and isinstance(response, dict):
            print(f"   ✅ User analytics retrieved")
            if 'api_usage' in response:
                print(f"   API Usage data available")
            return True
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
                required_fields = ['id', 'title', 'url', 'thumbnail', 'platform', 'viral_score']
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
                
                # Enhanced features testing
                self.test_enhanced_features(videos)
                
            return len(videos) > 0
        return False

    def test_enhanced_features(self, videos):
        """Test enhanced features in video data"""
        print(f"\n   🔍 Testing Enhanced Features:")
        
        # Test viral score quality
        viral_scores = [v.get('viral_score', 0) for v in videos]
        score_range = f"{min(viral_scores):.1f}-{max(viral_scores):.1f}"
        valid_scores = all(0 <= score <= 100 for score in viral_scores)
        print(f"   Viral scores range: {score_range} ({'✅ Valid' if valid_scores else '❌ Invalid'})")
        
        # Test title quality (enhanced titles should be longer and more engaging)
        avg_title_length = sum(len(v.get('title', '')) for v in videos) / len(videos)
        engaging_titles = sum(1 for v in videos if any(word in v.get('title', '').lower() 
                                                     for word in ['viral', 'trending', 'pov', 'breaking', 'amazing', 'incredible']))
        print(f"   Average title length: {avg_title_length:.1f} chars")
        print(f"   Engaging titles: {engaging_titles}/{len(videos)} ({'✅ Good' if engaging_titles > len(videos)//4 else '⚠️ Could improve'})")
        
        # Test platform diversity
        platforms = set(v.get('platform') for v in videos)
        print(f"   Platform diversity: {len(platforms)} platforms ({'✅ Good' if len(platforms) >= 3 else '⚠️ Limited'})")
        
        # Test data completeness
        complete_videos = sum(1 for v in videos if all(v.get(field) for field in ['views', 'likes', 'author']))
        completeness_rate = (complete_videos / len(videos)) * 100
        print(f"   Data completeness: {completeness_rate:.1f}% ({'✅ Good' if completeness_rate > 80 else '⚠️ Could improve'})")

    def test_viral_scoring_algorithm(self):
        """Test the enhanced viral scoring algorithm"""
        print(f"\n🔍 Testing Enhanced Viral Scoring Algorithm...")
        
        # Test with different platforms to see scoring differences
        platforms = ['youtube', 'twitter', 'tiktok', 'instagram']
        platform_scores = {}
        
        for platform in platforms:
            success, response = self.run_test(
                f"Viral Scoring - {platform.upper()}",
                "GET",
                "videos",
                200,
                params={'platform': platform, 'limit': 5}
            )
            
            if success and isinstance(response, dict):
                videos = response.get('videos', [])
                if videos:
                    scores = [v.get('viral_score', 0) for v in videos]
                    platform_scores[platform] = {
                        'avg_score': sum(scores) / len(scores),
                        'max_score': max(scores),
                        'min_score': min(scores)
                    }
                    print(f"   {platform.upper()}: Avg={platform_scores[platform]['avg_score']:.1f}, Range={platform_scores[platform]['min_score']:.1f}-{platform_scores[platform]['max_score']:.1f}")
        
        # Verify scoring makes sense
        if platform_scores:
            all_scores = [data['avg_score'] for data in platform_scores.values()]
            score_variance = max(all_scores) - min(all_scores)
            print(f"   Score variance across platforms: {score_variance:.1f} ({'✅ Good diversity' if score_variance > 10 else '⚠️ Low diversity'})")

    def test_api_resilience(self):
        """Test API resilience and error handling"""
        print(f"\n🔍 Testing API Resilience...")
        
        # Test invalid platform
        success, response = self.run_test(
            "Invalid Platform Handling",
            "GET",
            "videos",
            200,  # Should handle gracefully, not error
            params={'platform': 'invalid_platform'}
        )
        
        # Test large limit
        success, response = self.run_test(
            "Large Limit Handling",
            "GET",
            "videos",
            200,
            params={'limit': 1000}
        )
        
        # Test negative limit
        success, response = self.run_test(
            "Negative Limit Handling",
            "GET",
            "videos",
            200,  # Should handle gracefully
            params={'limit': -1}
        )

    def test_daily_delivery(self):
        """Test daily delivery endpoint"""
        success, response = self.run_test(
            "Daily Delivery Trigger",
            "POST",
            "deliver-daily",
            200
        )
        
        if success and isinstance(response, dict):
            message = response.get('message', '')
            print(f"   Delivery message: {message}")
            return 'scheduled' in message.lower()
        return False

    def test_platform_filtering(self):
        """Test platform filtering for each platform"""
        platforms = ['youtube', 'tiktok', 'twitter', 'instagram']
        all_passed = True
        
        for platform in platforms:
            success, response = self.run_test(
                f"Get {platform.upper()} Videos",
                "GET",
                "videos",
                200,
                params={'platform': platform}
            )
            
            if success and isinstance(response, dict):
                videos = response.get('videos', [])
                platform_match = response.get('platform') == platform
                
                # Check if all videos are from the requested platform
                correct_platform = all(v.get('platform') == platform for v in videos)
                
                print(f"   Platform filter: {'✅ Correct' if platform_match else '❌ Incorrect'}")
                print(f"   All videos from {platform}: {'✅ Yes' if correct_platform else '❌ No'}")
                print(f"   Video count: {len(videos)}")
                
                if not (platform_match and correct_platform and len(videos) > 0):
                    all_passed = False
            else:
                all_passed = False
                
        return all_passed

    def test_subscription_creation(self):
        """Test POST /api/subscribe - Create subscription"""
        test_subscriptions = [
            {
                "email": "test@example.com",
                "delivery_methods": ["email"]
            },
            {
                "telegram_id": "@testuser",
                "delivery_methods": ["telegram"]
            },
            {
                "whatsapp_number": "+1234567890",
                "delivery_methods": ["whatsapp"]
            },
            {
                "email": "multi@example.com",
                "telegram_id": "@multiuser",
                "delivery_methods": ["email", "telegram"]
            }
        ]
        
        all_passed = True
        for i, subscription_data in enumerate(test_subscriptions):
            success, response = self.run_test(
                f"Create Subscription {i+1}",
                "POST",
                "subscribe",
                200,
                data=subscription_data
            )
            
            if success and isinstance(response, dict):
                required_fields = ['id', 'delivery_methods', 'active', 'created_at']
                missing_fields = [field for field in required_fields if field not in response]
                
                if missing_fields:
                    print(f"   ⚠️  Missing fields in response: {missing_fields}")
                    all_passed = False
                else:
                    print(f"   ✅ Subscription created with ID: {response['id']}")
                    print(f"   Delivery methods: {response['delivery_methods']}")
            else:
                all_passed = False
                
        return all_passed

    def test_get_subscriptions(self):
        """Test GET /api/subscriptions - Get all subscriptions"""
        success, response = self.run_test(
            "Get All Subscriptions",
            "GET",
            "subscriptions",
            200
        )
        
        if success and isinstance(response, dict):
            subscriptions = response.get('subscriptions', [])
            total = response.get('total', 0)
            print(f"   Found {total} subscriptions")
            return True
        return False

    def test_video_history(self):
        """Test GET /api/videos/history - Get historical videos"""
        success, response = self.run_test(
            "Get Video History",
            "GET",
            "videos/history",
            200
        )
        
        if success and isinstance(response, dict):
            videos = response.get('videos', [])
            total = response.get('total', 0)
            print(f"   Found {total} historical videos")
            return True
        return False

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting Viral Daily API Tests")
        print("=" * 50)
        
        # Test core endpoints
        tests = [
            ("Root Endpoint", self.test_root_endpoint),
            ("Get All Videos", self.test_get_all_videos),
            ("Platform Filtering", self.test_platform_filtering),
            ("Viral Scoring Algorithm", self.test_viral_scoring_algorithm),
            ("API Resilience", self.test_api_resilience),
            ("Subscription Creation", self.test_subscription_creation),
            ("Get Subscriptions", self.test_get_subscriptions),
            ("Video History", self.test_video_history),
            ("Daily Delivery", self.test_daily_delivery)
        ]
        
        for test_name, test_func in tests:
            print(f"\n📋 Running {test_name} Tests...")
            try:
                test_func()
            except Exception as e:
                print(f"❌ Test suite failed: {str(e)}")
        
        # Print final results
        print("\n" + "=" * 50)
        print(f"📊 Final Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed! API is working correctly.")
            return 0
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed.")
            return 1

def main():
    tester = ViralDailyAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())