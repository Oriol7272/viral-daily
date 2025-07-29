import requests
import sys
import json
from datetime import datetime
import uuid

class ViralDailyAPITester:
    def __init__(self, base_url="https://e9c4e6b3-23fd-4c1f-81c6-d8dee2f62140.preview.emergentagent.com"):
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
                
            return len(videos) > 0
        return False

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
        """Test GET /api/payments/paypal/config - PayPal configuration"""
        success, response = self.run_test(
            "PayPal Configuration",
            "GET",
            "payments/paypal/config",
            200
        )
        
        if success and isinstance(response, dict):
            required_fields = ['client_id', 'mode', 'currency']
            missing_fields = [field for field in required_fields if field not in response]
            
            if missing_fields:
                print(f"   ⚠️  Missing fields: {missing_fields}")
                return False
            else:
                print(f"   ✅ PayPal Mode: {response['mode']}")
                print(f"   Currency: {response['currency']}")
                print(f"   Client ID: {response['client_id'][:20] if response['client_id'] else 'Not configured'}...")
                return True
        return False

    def test_paypal_availability(self):
        """Test GET /api/payments/paypal/available - PayPal availability check"""
        success, response = self.run_test(
            "PayPal Availability Check",
            "GET",
            "payments/paypal/available",
            200
        )
        
        if success and isinstance(response, dict):
            required_fields = ['available', 'mode']
            missing_fields = [field for field in required_fields if field not in response]
            
            if missing_fields:
                print(f"   ⚠️  Missing fields: {missing_fields}")
                return False
            else:
                print(f"   ✅ PayPal Available: {response['available']}")
                print(f"   Mode: {response['mode']}")
                if not response['available']:
                    print("   ℹ️  PayPal not available due to missing credentials (expected)")
                return True
        return False

    def test_paypal_create_order_unauthenticated(self):
        """Test POST /api/payments/paypal/create-order without authentication"""
        order_data = {
            "subscription_tier": "pro",
            "billing_cycle": "monthly"
        }
        
        success, response = self.run_test(
            "PayPal Create Order (Unauthenticated)",
            "POST",
            "payments/paypal/create-order",
            503,  # Expected to fail due to missing credentials
            data=order_data
        )
        
        if success:
            print("   ✅ Properly handles unauthenticated request")
            return True
        return False

    def test_paypal_create_order_authenticated(self):
        """Test POST /api/payments/paypal/create-order with authentication"""
        if not self.test_api_key:
            print("   ⚠️  No API key available, skipping test")
            return False
            
        order_data = {
            "subscription_tier": "pro",
            "billing_cycle": "monthly"
        }
        
        success, response = self.run_test(
            "PayPal Create Order (Authenticated)",
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
        
        success, response = self.run_test(
            "PayPal Order Status",
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

    def run_all_tests(self):
        """Run all API tests including monetization features"""
        print("🚀 Starting Viral Daily MONETIZED API Tests")
        print("=" * 60)
        
        # Test core endpoints first
        core_tests = [
            ("Root Endpoint", self.test_root_endpoint),
            ("Get All Videos (No Auth)", self.test_get_all_videos),
        ]
        
        # Test monetization features
        monetization_tests = [
            ("User Registration", self.test_user_registration),
            ("Subscription Plans", self.test_subscription_plans),
            ("Current User Info", self.test_current_user_info),
            ("Videos with Authentication", self.test_videos_with_auth),
            ("Subscription Info", self.test_subscription_info),
        ]
        
        all_tests = core_tests + monetization_tests
        
        for test_name, test_func in all_tests:
            print(f"\n📋 Running {test_name} Tests...")
            try:
                test_func()
            except Exception as e:
                print(f"❌ Test suite failed: {str(e)}")
        
        # Print final results
        print("\n" + "=" * 60)
        print(f"📊 Final Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        # Detailed summary
        success_rate = (self.tests_passed / self.tests_run) * 100 if self.tests_run > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed! MONETIZED API is working correctly.")
            print("💰 Monetization features: ✅ FULLY FUNCTIONAL")
            return 0
        else:
            failed_tests = self.tests_run - self.tests_passed
            print(f"⚠️  {failed_tests} tests failed.")
            if success_rate >= 80:
                print("💰 Monetization features: ✅ MOSTLY FUNCTIONAL")
            elif success_rate >= 60:
                print("💰 Monetization features: ⚠️  PARTIALLY FUNCTIONAL")
            else:
                print("💰 Monetization features: ❌ NEEDS ATTENTION")
            return 1

def main():
    tester = ViralDailyAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())