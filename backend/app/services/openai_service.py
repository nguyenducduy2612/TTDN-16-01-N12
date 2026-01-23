"""
OpenAI Service - Function Calling Integration
Handles AI chat processing with function calling for meeting room queries
"""
from openai import OpenAI
from typing import List, Dict, Optional, Any
import json
from datetime import datetime, timedelta
from ..config import settings
from .odoo_service import odoo_service
class OpenAIService:
    """Service for OpenAI chat with function calling"""
    
    def __init__(self):
        """Initialize OpenAI client"""
        # Initialize client with optional custom base URL
        client_kwargs = {"api_key": settings.openai_api_key}
        if settings.openai_base_url:
            client_kwargs["base_url"] = settings.openai_base_url
        
        self.client = OpenAI(**client_kwargs)
        self.model = settings.openai_model
        
        # Define function schemas
        self.functions = [
            {
                "name": "search_available_rooms",
                "description": "Tìm kiếm phòng họp rảnh trong khoảng thời gian. Dùng khi user hỏi về phòng nào rảnh, phòng trống, hoặc muốn đặt phòng.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "date_from": {
                            "type": "string",
                            "description": "Thời gian bắt đầu (format: YYYY-MM-DD HH:MM:SS). Ví dụ: '2024-01-20 09:00:00'"
                        },
                        "date_to": {
                            "type": "string",
                            "description": "Thời gian kết thúc (format: YYYY-MM-DD HH:MM:SS). Ví dụ: '2024-01-20 11:00:00'"
                        },
                        "min_capacity": {
                            "type": "integer",
                            "description": "Sức chứa tối thiểu (số người). Optional."
                        }
                    },
                    "required": ["date_from", "date_to"]
                }
            },
            {
                "name": "get_room_status",
                "description": "Kiểm tra trạng thái hiện tại của một phòng họp cụ thể. Dùng khi user hỏi phòng X có rảnh không, phòng Y đang làm gì.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "room_name": {
                            "type": "string",
                            "description": "Tên phòng họp. Ví dụ: 'Phòng A', 'Phòng họp B'"
                        }
                    },
                    "required": ["room_name"]
                }
            },
            {
                "name": "get_room_bookings",
                "description": "Xem lịch đặt phòng của một phòng họp trong khoảng thời gian. Dùng khi user hỏi lịch phòng, phòng được đặt khi nào.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "room_name": {
                            "type": "string",
                            "description": "Tên phòng họp"
                        },
                        "date_from": {
                            "type": "string",
                            "description": "Thời gian bắt đầu (format: YYYY-MM-DD HH:MM:SS). Optional, mặc định là hiện tại."
                        },
                        "date_to": {
                            "type": "string",
                            "description": "Thời gian kết thúc (format: YYYY-MM-DD HH:MM:SS). Optional, mặc định là 7 ngày sau."
                        }
                    },
                    "required": ["room_name"]
                }
            },
            {
                "name": "get_all_rooms",
                "description": "Lấy danh sách tất cả phòng họp. Dùng khi user hỏi có những phòng nào, liệt kê phòng họp.",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "get_room_info",
                "description": "Xem thông tin chi tiết của một phòng họp bao gồm sức chứa, vị trí, trạng thái và lịch sắp tới. Dùng khi user muốn biết chi tiết về một phòng.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "room_name": {
                            "type": "string",
                            "description": "Tên phòng họp"
                        }
                    },
                    "required": ["room_name"]
                }
            }
        ]
    
    def _execute_function(self, function_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Execute a function call by routing to the appropriate Odoo service method
        
        Args:
            function_name: Name of the function to execute
            arguments: Function arguments
        
        Returns:
            Function execution result
        """
        if function_name == "search_available_rooms":
            return odoo_service.search_available_rooms(
                date_from=arguments.get("date_from"),
                date_to=arguments.get("date_to"),
                min_capacity=arguments.get("min_capacity")
            )
        
        elif function_name == "get_room_status":
            return odoo_service.get_room_status(
                room_name=arguments.get("room_name")
            )
        
        elif function_name == "get_room_bookings":
            return odoo_service.get_room_bookings(
                room_name=arguments.get("room_name"),
                date_from=arguments.get("date_from"),
                date_to=arguments.get("date_to")
            )
        
        elif function_name == "get_all_rooms":
            return odoo_service.get_all_rooms()
        
        elif function_name == "get_room_info":
            return odoo_service.get_room_info(
                room_name=arguments.get("room_name")
            )
        
        else:
            return {"error": f"Unknown function: {function_name}"}
    
    def process_chat(
        self, 
        user_message: str, 
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Process a chat message with function calling support
        
        Args:
            user_message: User's message
            conversation_history: Previous conversation messages (optional)
        
        Returns:
            Dict containing response, function_called, and function_result
        """
        # Build messages array
        messages = conversation_history or []
        
        # Add system message if this is the first message
        if not messages:
            messages.append({
                "role": "system",
                "content": """Bạn là trợ lý AI thông minh cho hệ thống quản lý phòng họp.
Nhiệm vụ của bạn là giúp người dùng:
- Tìm phòng họp rảnh
- Kiểm tra trạng thái phòng
- Xem lịch đặt phòng
- Tra cứu thông tin phòng họp
Hãy trả lời bằng tiếng Việt, thân thiện và chuyên nghiệp.
Khi user hỏi về thời gian mơ hồ (ví dụ: "hôm nay", "tuần này", "ngày mai"), hãy tự động chuyển đổi sang datetime cụ thể.
Ngày hiện tại: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        
        # Add user message
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        # First API call - let GPT decide if it needs to call a function
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            functions=self.functions,
            function_call="auto"
        )
        
        response_message = response.choices[0].message
        
        # Check if GPT wants to call a function
        if response_message.function_call:
            # Extract function details
            function_name = response_message.function_call.name
            function_args = json.loads(response_message.function_call.arguments)
            
            # Execute the function
            function_result = self._execute_function(function_name, function_args)
            
            # Add assistant's function call to messages
            messages.append({
                "role": "assistant",
                "content": None,
                "function_call": {
                    "name": function_name,
                    "arguments": response_message.function_call.arguments
                }
            })
            
            # Add function result to messages
            messages.append({
                "role": "function",
                "name": function_name,
                "content": json.dumps(function_result, ensure_ascii=False)
            })
            
            # Second API call - let GPT format the response based on function result
            second_response = self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )
            
            final_response = second_response.choices[0].message.content
            
            return {
                "response": final_response,
                "function_called": function_name,
                "function_arguments": function_args,
                "function_result": function_result,
                "conversation_history": messages
            }
        
        else:
            # No function call needed, just return the response
            return {
                "response": response_message.content,
                "function_called": None,
                "function_result": None,
                "conversation_history": messages
            }
    
    def parse_natural_time(self, time_expression: str) -> Dict[str, str]:
        """
        Helper method to parse natural language time expressions
        (Can be used by the API layer if needed)
        
        Args:
            time_expression: Natural language time (e.g., "hôm nay", "tuần này")
        
        Returns:
            Dict with date_from and date_to
        """
        now = datetime.now()
        
        # Common patterns
        if "hôm nay" in time_expression.lower():
            date_from = now.replace(hour=8, minute=0, second=0)
            date_to = now.replace(hour=18, minute=0, second=0)
        
        elif "ngày mai" in time_expression.lower():
            tomorrow = now + timedelta(days=1)
            date_from = tomorrow.replace(hour=8, minute=0, second=0)
            date_to = tomorrow.replace(hour=18, minute=0, second=0)
        
        elif "tuần này" in time_expression.lower():
            # From today to end of week (Sunday)
            date_from = now.replace(hour=8, minute=0, second=0)
            days_until_sunday = 6 - now.weekday()
            date_to = (now + timedelta(days=days_until_sunday)).replace(hour=18, minute=0, second=0)
        
        elif "tuần sau" in time_expression.lower():
            # Next Monday to next Sunday
            days_until_next_monday = 7 - now.weekday()
            next_monday = now + timedelta(days=days_until_next_monday)
            date_from = next_monday.replace(hour=8, minute=0, second=0)
            date_to = (next_monday + timedelta(days=6)).replace(hour=18, minute=0, second=0)
        
        else:
            # Default: next 7 days
            date_from = now.replace(hour=8, minute=0, second=0)
            date_to = (now + timedelta(days=7)).replace(hour=18, minute=0, second=0)
        
        return {
            "date_from": date_from.strftime('%Y-%m-%d %H:%M:%S'),
            "date_to": date_to.strftime('%Y-%m-%d %H:%M:%S')
        }
# Global instance
openai_service = OpenAIService()
