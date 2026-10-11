"""
Conversational Travel AI Endpoint (Groq LLM Powered)
===================================================
Enables interactive chat assistance across the platform.
Supports tool-calling for real-time train delay predictions,
connecting bus routes, upstream quota arbitrage, and multimodal route discovery.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.llm_chat_service import run_chat_completion

router = APIRouter()


class ChatMessage(BaseModel):
    role: str = Field(..., description="'user' or 'assistant'")
    content: str = Field(..., description="Message text")


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User question or statement")
    conversation_history: Optional[List[ChatMessage]] = Field(default=[], description="Past messages")
    current_origin: Optional[str] = Field(None, description="Optional current search origin code or city")
    current_destination: Optional[str] = Field(None, description="Optional current search destination code or city")
    travel_date: Optional[str] = Field(None, description="Optional current search travel date")


class ChatResponse(BaseModel):
    reply: str
    suggested_actions: List[str] = []
    routes_preview: Optional[List[Dict[str, Any]]] = None
    buses_preview: Optional[List[Dict[str, Any]]] = None


@router.post("/chat", response_model=ChatResponse)
async def chat_with_assistant(request: ChatRequest):
    """
    Multimodal Travel AI Chat Endpoint.
    Grounded with real-time train timetables, delay predictions, and 1,138 bus corridors.
    """
    try:
        history_dicts = [
            {"role": m.role, "content": m.content}
            for m in (request.conversation_history or [])
        ]
        result = await run_chat_completion(
            message=request.message,
            conversation_history=history_dicts,
            current_origin=request.current_origin,
            current_destination=request.current_destination,
            travel_date=request.travel_date,
        )
        return ChatResponse(
            reply=result.get("reply", ""),
            suggested_actions=result.get("suggested_actions", []),
            routes_preview=result.get("routes_preview"),
            buses_preview=result.get("buses_preview"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")
