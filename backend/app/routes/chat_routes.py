from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime


from backend.app.config import REFLECTION
from backend.app.services.llm_client import generate_response, health_check
from backend.app.utils.prompt_templates import AITutorPrompt


router = APIRouter()


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]
    max_tokens: Optional[int] = 800


class ChatResponse(BaseModel):
    response: str
    processing_time: float


@router.get("/health")
async def check_health():
    """Kiểm tra trạng thái hoạt động của API"""
    llm_status = health_check()
    return {
        "status": "healthy",
        "llm_connection": llm_status,
    }


@router.post("/chat", response_model=ChatResponse)
async def process_message(request: ChatRequest):
    """
    Xử lý tin nhắn người dùng và trả về phản hồi từ LLM.

    Args:
        request: Yêu cầu chứa danh sách tin nhắn.

    Returns:
        ChatResponse: Phản hồi từ LLM và thời gian xử lý.
    """
    start_time = datetime.now()

    try:
        # Chuyển đổi từ Pydantic models sang dict
        history = [{"role": msg.role, "content": msg.content} for msg in request.messages]

        # Lấy lịch sử gần nhất
        latest_history = REFLECTION(history, last_items_considered=8)

        # Tạo prompt
        prompt = AITutorPrompt(history=latest_history).format()

        # Gọi API LLM
        stream = generate_response(prompt, max_tokens=request.max_tokens)
        response_text = ""

        # Xử lý stream phản hồi
        for event in stream:
            if event.choices[0].text:
                response_text += event.choices[0].text

        # Tính thời gian xử lý
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()

        return ChatResponse(
            response=response_text,
            processing_time=processing_time
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi xử lý tin nhắn: {str(e)}")