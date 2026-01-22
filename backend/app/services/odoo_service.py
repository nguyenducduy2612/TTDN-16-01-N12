"""
Odoo Service - XML-RPC Integration
Handles all communication with Odoo database for meeting room data
"""
import xmlrpc.client
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from ..config import settings
class OdooService:
    """Service for interacting with Odoo via XML-RPC"""
    
    def __init__(self):
        """Initialize Odoo connection"""
        self.url = settings.odoo_url
        self.db = settings.odoo_db
        self.username = settings.odoo_username
        self.password = settings.odoo_password
        
        # XML-RPC endpoints
        self.common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
        self.models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')
        
        # Authenticate and get user ID
        self.uid = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Odoo and store user ID"""
        try:
            self.uid = self.common.authenticate(
                self.db, 
                self.username, 
                self.password, 
                {}
            )
            if not self.uid:
                raise Exception("Authentication failed - Invalid credentials")
        except Exception as e:
            raise Exception(f"Failed to connect to Odoo: {str(e)}")
    
    def _execute(self, model: str, method: str, *args, **kwargs) -> Any:
        """Execute a method on an Odoo model"""
        return self.models.execute_kw(
            self.db, 
            self.uid, 
            self.password,
            model, 
            method, 
            args, 
            kwargs
        )
    
    def search_available_rooms(
        self, 
        date_from: str, 
        date_to: str, 
        min_capacity: Optional[int] = None
    ) -> List[Dict]:
        """
        Search for available rooms in a time range
        
        Args:
            date_from: Start datetime (ISO format: YYYY-MM-DD HH:MM:SS)
            date_to: End datetime (ISO format: YYYY-MM-DD HH:MM:SS)
            min_capacity: Minimum room capacity (optional)
        
        Returns:
            List of available rooms with basic info
        """
        # Get all rooms
        domain = []
        if min_capacity:
            domain.append(('capacity', '>=', min_capacity))
        
        rooms = self._execute(
            'meeting.room',
            'search_read',
            domain,
            {'fields': ['id', 'name', 'capacity', 'location']}
        )
        
        # Filter out rooms with approved bookings in the time range
        available_rooms = []
        for room in rooms:
            # Check if room has any approved bookings in the time range
            booking_count = self._execute(
                'meeting.booking',
                'search_count',
                [
                    ('meeting_room_id', '=', room['id']),
                    ('state', '=', 'approved'),
                    ('start_time', '<', date_to),
                    ('end_time', '>', date_from)
                ]
            )
            
            if booking_count == 0:
                available_rooms.append({
                    'id': room['id'],
                    'name': room['name'],
                    'capacity': room['capacity'],
                    'location': room['location'] or 'Chưa cập nhật'
                })
        
        return available_rooms
    
    def get_room_status(self, room_name: str) -> Dict:
        """
        Get current status of a specific room
        
        Args:
            room_name: Name of the room
        
        Returns:
            Room status information
        """
        # Find room by name
        rooms = self._execute(
            'meeting.room',
            'search_read',
            [('name', 'ilike', room_name)],
            {'fields': ['id', 'name', 'capacity', 'location', 'manual_status'], 'limit': 1}
        )
        
        if not rooms:
            return {
                'found': False,
                'message': f'Không tìm thấy phòng "{room_name}"'
            }
        
        room = rooms[0]
        
        # Check if room is in maintenance
        if room.get('manual_status') == 'maintenance':
            return {
                'found': True,
                'room_name': room['name'],
                'status': 'maintenance',
                'status_text': 'Đang bảo trì',
                'capacity': room['capacity'],
                'location': room['location'] or 'Chưa cập nhật'
            }
        
        # Check if room has current booking
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        current_bookings = self._execute(
            'meeting.booking',
            'search_read',
            [
                ('meeting_room_id', '=', room['id']),
                ('state', '=', 'approved'),
                ('start_time', '<=', now),
                ('end_time', '>', now)
            ],
            {'fields': ['description', 'start_time', 'end_time'], 'limit': 1}
        )
        
        if current_bookings:
            booking = current_bookings[0]
            return {
                'found': True,
                'room_name': room['name'],
                'status': 'occupied',
                'status_text': 'Đang sử dụng',
                'capacity': room['capacity'],
                'location': room['location'] or 'Chưa cập nhật',
                'current_booking': {
                    'description': booking['description'],
                    'start_time': booking['start_time'],
                    'end_time': booking['end_time']
                }
            }
        
        return {
            'found': True,
            'room_name': room['name'],
            'status': 'free',
            'status_text': 'Rảnh',
            'capacity': room['capacity'],
            'location': room['location'] or 'Chưa cập nhật'
        }
    
    def get_room_bookings(
        self, 
        room_name: str, 
        date_from: Optional[str] = None, 
        date_to: Optional[str] = None
    ) -> Dict:
        """
        Get bookings for a specific room in a time range
        
        Args:
            room_name: Name of the room
            date_from: Start datetime (ISO format, optional - defaults to now)
            date_to: End datetime (ISO format, optional - defaults to 7 days from now)
        
        Returns:
            Room bookings information
        """
        # Find room by name
        rooms = self._execute(
            'meeting.room',
            'search_read',
            [('name', 'ilike', room_name)],
            {'fields': ['id', 'name'], 'limit': 1}
        )
        
        if not rooms:
            return {
                'found': False,
                'message': f'Không tìm thấy phòng "{room_name}"'
            }
        
        room = rooms[0]
        
        # Set default date range if not provided
        if not date_from:
            date_from = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if not date_to:
            date_to = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
        
        # Get approved bookings in the time range
        bookings = self._execute(
            'meeting.booking',
            'search_read',
            [
                ('meeting_room_id', '=', room['id']),
                ('state', '=', 'approved'),
                ('start_time', '<', date_to),
                ('end_time', '>', date_from)
            ],
            {
                'fields': ['description', 'start_time', 'end_time', 'organizer_id'],
                'order': 'start_time asc'
            }
        )
        
        # Format bookings
        formatted_bookings = []
        for booking in bookings:
            formatted_bookings.append({
                'description': booking['description'],
                'start_time': booking['start_time'],
                'end_time': booking['end_time'],
                'organizer': booking['organizer_id'][1] if booking.get('organizer_id') else 'N/A'
            })
        
        return {
            'found': True,
            'room_name': room['name'],
            'bookings': formatted_bookings,
            'total_bookings': len(formatted_bookings),
            'date_from': date_from,
            'date_to': date_to
        }
    
    def get_all_rooms(self) -> List[Dict]:
        """
        Get list of all meeting rooms
        
        Returns:
            List of all rooms with basic information
        """
        rooms = self._execute(
            'meeting.room',
            'search_read',
            [],
            {
                'fields': ['name', 'capacity', 'location', 'manual_status'],
                'order': 'name asc'
            }
        )
        
        # Format room data
        formatted_rooms = []
        for room in rooms:
            # Determine current status
            status = 'free'
            if room.get('manual_status') == 'maintenance':
                status = 'maintenance'
            else:
                # Check for current booking
                now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                booking_count = self._execute(
                    'meeting.booking',
                    'search_count',
                    [
                        ('meeting_room_id', '=', room['id']),
                        ('state', '=', 'approved'),
                        ('start_time', '<=', now),
                        ('end_time', '>', now)
                    ]
                )
                if booking_count > 0:
                    status = 'occupied'
            
            formatted_rooms.append({
                'name': room['name'],
                'capacity': room['capacity'],
                'location': room['location'] or 'Chưa cập nhật',
                'status': status
            })
        
        return formatted_rooms
    
    def get_room_info(self, room_name: str) -> Dict:
        """
        Get detailed information about a room including upcoming bookings
        
        Args:
            room_name: Name of the room
        
        Returns:
            Detailed room information
        """
        # Find room by name
        rooms = self._execute(
            'meeting.room',
            'search_read',
            [('name', 'ilike', room_name)],
            {
                'fields': ['id', 'name', 'capacity', 'location', 'manual_status', 
                          'booking_count', 'total_hours_used'],
                'limit': 1
            }
        )
        
        if not rooms:
            return {
                'found': False,
                'message': f'Không tìm thấy phòng "{room_name}"'
            }
        
        room = rooms[0]
        
        # Get current status
        status = 'free'
        current_booking = None
        
        if room.get('manual_status') == 'maintenance':
            status = 'maintenance'
        else:
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            current_bookings = self._execute(
                'meeting.booking',
                'search_read',
                [
                    ('meeting_room_id', '=', room['id']),
                    ('state', '=', 'approved'),
                    ('start_time', '<=', now),
                    ('end_time', '>', now)
                ],
                {'fields': ['description', 'start_time', 'end_time', 'organizer_id'], 'limit': 1}
            )
            
            if current_bookings:
                status = 'occupied'
                booking = current_bookings[0]
                current_booking = {
                    'description': booking['description'],
                    'start_time': booking['start_time'],
                    'end_time': booking['end_time'],
                    'organizer': booking['organizer_id'][1] if booking.get('organizer_id') else 'N/A'
                }
        
        # Get upcoming bookings (next 7 days)
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        future_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
        
        upcoming_bookings = self._execute(
            'meeting.booking',
            'search_read',
            [
                ('meeting_room_id', '=', room['id']),
                ('state', '=', 'approved'),
                ('start_time', '>=', now),
                ('start_time', '<', future_date)
            ],
            {
                'fields': ['description', 'start_time', 'end_time', 'organizer_id'],
                'order': 'start_time asc',
                'limit': 5
            }
        )
        
        formatted_upcoming = []
        for booking in upcoming_bookings:
            formatted_upcoming.append({
                'description': booking['description'],
                'start_time': booking['start_time'],
                'end_time': booking['end_time'],
                'organizer': booking['organizer_id'][1] if booking.get('organizer_id') else 'N/A'
            })
        
        return {
            'found': True,
            'room_name': room['name'],
            'capacity': room['capacity'],
            'location': room['location'] or 'Chưa cập nhật',
            'status': status,
            'current_booking': current_booking,
            'upcoming_bookings': formatted_upcoming,
            'stats': {
                'total_bookings': room.get('booking_count', 0),
                'total_hours_used': round(room.get('total_hours_used', 0), 2)
            }
        }
# Global instance
odoo_service = OdooService()
