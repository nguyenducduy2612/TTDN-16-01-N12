"""
Chat Router - API Endpoints
Handles chat requests and health checks
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
import logging
from ..services.openai_service import openai_service

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Request/Response models
class ChatMessage(BaseModel):
    """Chat message model"""
    role: str = Field(..., description="Message role: user, assistant, system")
    content: str = Field(..., description="Message content")

class ChatRequest(BaseModel):
    """Chat request model"""
    message: str = Field(..., description="User's message", min_length=1)
    conversation_history: Optional[List[Dict]] = Field(
        default=None, 
        description="Previous conversation messages (optional)"
    )

class ChatResponse(BaseModel):
    """Chat response model"""
    response: str = Field(..., description="AI's response")
    function_called: Optional[str] = Field(None, description="Name of function called (if any)")
    function_arguments: Optional[Dict[str, Any]] = Field(None, description="Arguments passed to function")
    function_result: Optional[Any] = Field(None, description="Result from function execution")
    conversation_history: List[Dict] = Field(..., description="Updated conversation history")

class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="API version")

# Endpoints
@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with AI chatbot
    
    Process user's message and return AI response with optional function calling.
    The AI can automatically query Odoo for meeting room information.
    
    **Example requests:**
    - "Có những phòng họp nào?"
    - "Phòng A có rảnh không?"
    - "Tuần này có phòng nào trống?"
    - "Cho tôi xem lịch phòng B"
    """
    try:
        logger.info(f"📨 Received chat request: {request.message[:50]}...")
        
        # Process chat with OpenAI
        result = openai_service.process_chat(
            user_message=request.message,
            conversation_history=request.conversation_history
        )
        
        # Log function call if any
        if result.get("function_called"):
            logger.info(f"🔧 Function called: {result['function_called']}")
            logger.info(f"📊 Function result: {str(result['function_result'])[:100]}...")
        
        logger.info(f"✅ Response generated successfully")
        
        return ChatResponse(
            response=result["response"],
            function_called=result.get("function_called"),
            function_arguments=result.get("function_arguments"),
            function_result=result.get("function_result"),
            conversation_history=result["conversation_history"]
        )
    
    except Exception as e:
        logger.error(f"❌ Error processing chat: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat request: {str(e)}"
        )

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    
    Returns the current status of the API service.
    """
    return HealthResponse(
        status="healthy",
        service="AI Chatbot Backend",
        version="1.0.0"
    )
