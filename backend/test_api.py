"""
Test Script for AI Chatbot Backend API
Run this script to test the API endpoints
"""
import requests
import json
from datetime import datetime, timedelta

# API Base URL
BASE_URL = "http://localhost:8000"

def print_section(title):
    """Print a section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_health_check():
    """Test health check endpoint"""
    print_section("1. Testing Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_chat(message, conversation_history=None):
    """Test chat endpoint"""
    print(f"\n📨 User: {message}")
    
    try:
        payload = {
            "message": message,
            "conversation_history": conversation_history or []
        }
        
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"🤖 AI: {data['response']}")
            
            if data.get('function_called'):
                print(f"\n🔧 Function Called: {data['function_called']}")
                print(f"📊 Arguments: {json.dumps(data['function_arguments'], indent=2, ensure_ascii=False)}")
                print(f"📋 Result Preview: {str(data['function_result'])[:200]}...")
            
            return data
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def run_tests():
    """Run all tests"""
    print("\n🚀 Starting API Tests...")
    print(f"📍 Base URL: {BASE_URL}")
    
    # Test 1: Health Check
    health_ok = test_health_check()
    if not health_ok:
        print("\n❌ Health check failed! Make sure the server is running.")
        return
    
    print("\n✅ Health check passed!")
    
    # Test 2: Chat Tests
    print_section("2. Testing Chat Endpoint")
    
    # Test 2.1: Get all rooms
    print("\n--- Test 2.1: Liệt kê tất cả phòng ---")
    result1 = test_chat("Có những phòng họp nào?")
    
    # Test 2.2: Check room status
    print("\n--- Test 2.2: Kiểm tra trạng thái phòng ---")
    result2 = test_chat("Phòng A có rảnh không?")
    
    # Test 2.3: Search available rooms
    print("\n--- Test 2.3: Tìm phòng rảnh ---")
    result3 = test_chat("Tuần này có phòng nào trống?")
    
    # Test 2.4: Get room info
    print("\n--- Test 2.4: Xem thông tin chi tiết phòng ---")
    result4 = test_chat("Cho tôi xem thông tin chi tiết về Phòng A")
    
    # Test 2.5: Get room bookings
    print("\n--- Test 2.5: Xem lịch đặt phòng ---")
    result5 = test_chat("Phòng B được đặt lúc nào trong tuần này?")
    
    # Test 2.6: Conversation with history
    print("\n--- Test 2.6: Hội thoại liên tục ---")
    if result1:
        conversation = result1.get('conversation_history', [])
        result6 = test_chat("Phòng đầu tiên có sức chứa bao nhiêu người?", conversation)
    
    # Summary
    print_section("Test Summary")
    print("✅ All tests completed!")
    print("\n💡 Tips:")
    print("  - Check the responses above for any errors")
    print("  - Make sure Odoo is running and accessible")
    print("  - Verify your .env configuration")
    print("  - Check server logs for detailed information")

if __name__ == "__main__":
    try:
        run_tests()
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {str(e)}")
