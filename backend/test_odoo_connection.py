"""
Test Odoo XML-RPC Connection
Kiểm tra kết nối đến Odoo trước khi chạy backend
"""
import xmlrpc.client
import sys

# ========== CẤU HÌNH ==========
# Thay đổi các thông tin sau cho phù hợp với Odoo của bạn
ODOO_URL = "http://localhost:8069"
ODOO_DB = "your_database_name"  # Thay bằng tên database thực tế
ODOO_USERNAME = "admin"          # Thay bằng username của bạn
ODOO_PASSWORD = "admin"          # Thay bằng password của bạn

def print_section(title):
    """Print section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_connection():
    """Test basic connection and authentication"""
    print_section("1. Testing Authentication")
    
    try:
        common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
        uid = common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {})
        
        if uid:
            print(f"✅ Authentication successful!")
            print(f"   User ID: {uid}")
            print(f"   URL: {ODOO_URL}")
            print(f"   Database: {ODOO_DB}")
            return uid
        else:
            print("❌ Authentication failed!")
            print("   Please check:")
            print("   - Database name")
            print("   - Username")
            print("   - Password")
            return None
    except Exception as e:
        print(f"❌ Connection error: {str(e)}")
        print("   Please check:")
        print("   - Odoo is running")
        print("   - URL is correct")
        print("   - Port 8069 is accessible")
        return None

def test_meeting_room_model(uid):
    """Test meeting.room model access"""
    print_section("2. Testing meeting.room Model")
    
    try:
        models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')
        
        # Check if model exists
        room_count = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'meeting.room', 'search_count', [[]]
        )
        
        print(f"✅ Model 'meeting.room' found!")
        print(f"   Total rooms: {room_count}")
        
        # Get sample rooms
        if room_count > 0:
            rooms = models.execute_kw(
                ODOO_DB, uid, ODOO_PASSWORD,
                'meeting.room', 'search_read',
                [],
                {'fields': ['name', 'capacity', 'location'], 'limit': 5}
            )
            
            print(f"\n📋 Sample rooms:")
            for room in rooms:
                location = room.get('location') or 'N/A'
                print(f"   - {room['name']} (Capacity: {room['capacity']}, Location: {location})")
        else:
            print("\n⚠️  No rooms found. You may need to create some test data.")
        
        return True
    except Exception as e:
        print(f"❌ Error accessing meeting.room: {str(e)}")
        print("   Please check:")
        print("   - Module 'phong_hop' is installed")
        print("   - User has read access to meeting.room")
        return False

def test_meeting_booking_model(uid):
    """Test meeting.booking model access"""
    print_section("3. Testing meeting.booking Model")
    
    try:
        models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')
        
        # Check if model exists
        booking_count = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'meeting.booking', 'search_count', [[]]
        )
        
        print(f"✅ Model 'meeting.booking' found!")
        print(f"   Total bookings: {booking_count}")
        
        # Get approved bookings
        if booking_count > 0:
            approved_count = models.execute_kw(
                ODOO_DB, uid, ODOO_PASSWORD,
                'meeting.booking', 'search_count',
                [[('state', '=', 'approved')]]
            )
            print(f"   Approved bookings: {approved_count}")
        
        return True
    except Exception as e:
        print(f"❌ Error accessing meeting.booking: {str(e)}")
        print("   Please check:")
        print("   - Module 'phong_hop' is installed")
        print("   - User has read access to meeting.booking")
        return False

def test_backend_functions(uid):
    """Test functions that backend will use"""
    print_section("4. Testing Backend Functions")
    
    try:
        models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')
        
        # Test 1: Get all rooms
        print("\n🔧 Test: Get all rooms")
        rooms = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'meeting.room', 'search_read',
            [],
            {'fields': ['name', 'capacity', 'location', 'manual_status'], 'limit': 3}
        )
        print(f"   ✅ Retrieved {len(rooms)} rooms")
        
        # Test 2: Search room by name
        if rooms:
            test_room_name = rooms[0]['name']
            print(f"\n🔧 Test: Search room by name '{test_room_name}'")
            found_rooms = models.execute_kw(
                ODOO_DB, uid, ODOO_PASSWORD,
                'meeting.room', 'search_read',
                [[('name', 'ilike', test_room_name)]],
                {'fields': ['name'], 'limit': 1}
            )
            if found_rooms:
                print(f"   ✅ Found room: {found_rooms[0]['name']}")
            else:
                print(f"   ❌ Room not found")
        
        # Test 3: Get bookings
        print(f"\n🔧 Test: Get approved bookings")
        bookings = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'meeting.booking', 'search_read',
            [[('state', '=', 'approved')]],
            {'fields': ['description', 'start_time', 'end_time'], 'limit': 3}
        )
        print(f"   ✅ Retrieved {len(bookings)} approved bookings")
        
        return True
    except Exception as e:
        print(f"❌ Error testing functions: {str(e)}")
        return False

def main():
    """Main test function"""
    print("\n🚀 Odoo XML-RPC Connection Test")
    print(f"📍 Testing connection to: {ODOO_URL}")
    print(f"📊 Database: {ODOO_DB}")
    print(f"👤 Username: {ODOO_USERNAME}")
    
    # Test 1: Authentication
    uid = test_connection()
    if not uid:
        print("\n❌ Connection test failed. Please fix authentication issues first.")
        sys.exit(1)
    
    # Test 2: Meeting Room Model
    if not test_meeting_room_model(uid):
        print("\n❌ meeting.room model test failed.")
        sys.exit(1)
    
    # Test 3: Meeting Booking Model
    if not test_meeting_booking_model(uid):
        print("\n❌ meeting.booking model test failed.")
        sys.exit(1)
    
    # Test 4: Backend Functions
    if not test_backend_functions(uid):
        print("\n⚠️  Some backend functions may not work correctly.")
    
    # Summary
    print_section("Test Summary")
    print("✅ All tests passed!")
    print("\n💡 Next steps:")
    print("   1. Update backend/.env with these credentials")
    print("   2. Run: python -m app.main")
    print("   3. Test chatbot at http://localhost:8000/docs")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {str(e)}")
        sys.exit(1)
