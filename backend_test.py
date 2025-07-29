import requests
import sys
import json
from datetime import datetime

class ViralDailyAPITester:
    def __init__(self, base_url="https://42ddaa94-2f87-4bfa-b3ea-e8e4d90c7075.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if endpoint else self.api_url
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)

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
        """Test GET /api/videos - Get all viral videos"""
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
                
            return len(videos) > 0
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
            ("Subscription Creation", self.test_subscription_creation),
            ("Get Subscriptions", self.test_get_subscriptions),
            ("Video History", self.test_video_history)
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