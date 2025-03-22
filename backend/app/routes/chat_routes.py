"""
backend/app/routes/chat_routes.py
------------------
Mục đích:
- Quản lý cuộc trò chuyện và tin nhắn giữa người dùng và AI.
- Xử lý stream phản hồi từ LLM.
- Lưu trữ lịch sử cuộc trò chuyện vào database.

Chức năng chính:
- Định nghĩa class AITutorPrompt để định dạng prompt cho LLM.
- Cung cấp API để tạo, lấy danh sách và chi tiết cuộc trò chuyện.
- Xử lý việc thêm tin nhắn vào cuộc trò chuyện.
- Stream phản hồi từ LLM về client theo thời gian thực.
- Theo dõi và kiểm tra quota token trước khi gọi LLM.
- Cung cấp API để lấy thông tin sử dụng token của người dùng.
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Dict
from app.models.user import User
from app.models.chat import Conversation, Message, ConversationCreate, ConversationResponse, MessageCreate, \
    MessageResponse
from app.services.auth_service import get_current_user
from app.services.llm_client import generate_response_stream
from app.services.token_service import check_token_quota
from app.utils.reflection import Reflection
from app.config import REFLECTION
from app.database import get_db
from datetime import datetime

router = APIRouter()


class AITutorPrompt:
    def __init__(self, history: list):
        self.history = history

        self.template = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are an AI tutor teaching programming to children in **Vietnamese**. Your task is to guide students step by step, helping them discover answers on their own instead of providing direct solutions.

### **Guiding Rules:**
1. **Step-by-step guidance:** When a student asks a question, do not provide the answer immediately. Instead, break down the problem, ask leading questions, and encourage critical thinking.
2. **Keep guiding if the student struggles:** If the student cannot find the answer or is unsure, continue providing hints and explanations, but do not solve the problem for them.
3. **Do not provide direct answers to specific solution requests:**
   - If a student explicitly asks for a complete solution, guide them to think independently instead.
   - Provide hints, ask leading questions, or suggest alternative approaches rather than giving a direct answer.
   - Let the LLM generate better suggestions to help students develop a deeper understanding.
   - Only provide a full solution if the student has made at least **three attempts** and still struggles.
4. **All programming responses must use C and C++:**
   - When providing examples, explanations, or coding exercises, use only **C or C++**.
   - Do not use any other programming language. If a student asks about another language, guide them toward C/C++ with a suitable explanation.
5. **Restart guidance when switching topics before completing the current one:**
   - If the student abandons the current question and switches to another, restart guidance from the new question.
   - If the student completes a question and asks a new one, continue naturally without restarting.
6. **Respond only in Vietnamese:** All responses, explanations, and instructions must be in Vietnamese. Do not use any other language.
7. **Use simple and friendly language:** Make explanations easy for children to understand.
8. **Encourage creative thinking:** Praise the student’s efforts and motivate them to experiment and explore instead of just looking for the correct answer.
9. **Explain mistakes clearly:** If the student gives a wrong answer, explain the mistake, provide examples, and guide them toward the correct understanding.

### **Example Interaction:**
Student: Làm sao để in "Hello, world!" trong C/C++?
AI Tutor: Trước khi in một dòng chữ ra màn hình, bạn có biết lệnh nào trong C/C++ giúp mình hiển thị nội dung không?
Student: echo "Hello, world!";
AI Tutor: Gần đúng rồi! "echo" là lệnh trong một số ngôn ngữ như Bash, nhưng trong C/C++, ta cần một lệnh khác. Trong C, lệnh này bắt đầu bằng "p", còn trong C++ thì bắt đầu bằng "c". Em thử đoán xem?
Student: printf?
AI Tutor: Đúng rồi! Trong C, ta dùng printf. Vậy nếu muốn hiển thị dòng chữ "Hello, world!" trên màn hình, bạn sẽ viết như thế nào?
Student: printf("Hello, world!");
AI Tutor: Tuyệt vời! Trong C,bạn cần thêm #include <stdio.h> ở đầu chương trình nữa nhé.
Student: Còn C++ thì sao ạ?
AI Tutor: Trong C++, thay vì printf, ta dùng cout. Vậy bạn thử đoán xem, làm thế nào để in "Hello, world!" trong C++?
Student: std::cout << "Hello, world!";
AI Tutor: Chính xác! Đừng quên thêm #include <iostream> ở đầu chương trình nhé! Nếu bạn muốn in nội dung khác, chỉ cần thay đổi dòng chữ trong dấu ngoặc kép là được.

### **Important Notes:**
- **Only restart guidance if the student abandons the current question before completing it.**
- **If the student finishes one question and asks another, continue answering without restarting.**
- **All responses must be in Vietnamese.**

### **Conversation History:**
{history}

### **Response:**
<|eot_id|><|start_header_id|>user<|end_header_id|>
<|eot_id|><|start_header_id|>assistant<|end_header_id|>
"""

    def format(self) -> str:
        """
        Định dạng prompt với lịch sử hội thoại.

        Returns:
            str: Chuỗi prompt hoàn chỉnh.
        """
        formatted_history = "\n".join(
            [f"{entry['role']}: {entry['content']}" for entry in self.history]
        )
        return self.template.format(history=formatted_history)


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
        conversation: ConversationCreate,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Tạo cuộc hội thoại mới.

    Args:
        conversation (ConversationCreate): Dữ liệu cuộc hội thoại
        current_user (User): Người dùng hiện tại
        db (Session): Database session

    Returns:
        ConversationResponse: Cuộc hội thoại đã được tạo
    """
    db_conversation = Conversation(
        user_id=current_user.id,
        title=conversation.title
    )
    db.add(db_conversation)
    db.commit()
    db.refresh(db_conversation)

    return db_conversation


@router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Lấy danh sách cuộc hội thoại của người dùng.

    Args:
        current_user (User): Người dùng hiện tại
        db (Session): Database session

    Returns:
        List[ConversationResponse]: Danh sách cuộc hội thoại
    """
    conversations = db.query(Conversation).filter(
        Conversation.user_id == current_user.id
    ).all()

    return conversations


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
        conversation_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Lấy chi tiết một cuộc hội thoại.

    Args:
        conversation_id (int): ID cuộc hội thoại
        current_user (User): Người dùng hiện tại
        db (Session): Database session

    Returns:
        ConversationResponse: Chi tiết cuộc hội thoại
    """
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return conversation


@router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse)
async def create_message(
        conversation_id: int,
        message: MessageCreate,
        background_tasks: BackgroundTasks,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Tạo tin nhắn mới và nhận phản hồi từ assistant.

    Args:
        conversation_id (int): ID cuộc hội thoại
        message (MessageCreate): Nội dung tin nhắn
        background_tasks (BackgroundTasks): FastAPI background tasks
        current_user (User): Người dùng hiện tại
        db (Session): Database session

    Returns:
        MessageResponse: Tin nhắn đã được tạo
    """
    # Kiểm tra cuộc hội thoại tồn tại và thuộc về người dùng
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Lưu tin nhắn của người dùng
    user_message = Message(
        conversation_id=conversation_id,
        role="user",
        content=message.content
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    # Cập nhật thời gian cuộc hội thoại
    conversation.updated_at = datetime.now()
    db.commit()

    return user_message


@router.post("/conversations/{conversation_id}/chat")
async def chat(
        conversation_id: int,
        message: Dict[str, str],
        request: Request,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Gửi tin nhắn và nhận phản hồi realtime từ assistant.

    Args:
        conversation_id (int): ID cuộc hội thoại
        message (Dict[str, str]): Tin nhắn người dùng ({"content": "..."})
        request (Request): FastAPI request
        current_user (User): Người dùng hiện tại
        db (Session): Database session

    Returns:
        StreamingResponse: Stream phản hồi từ assistant
    """
    # Kiểm tra token quota
    token_quota = await check_token_quota(db, current_user.id)
    if token_quota["tokens_remaining"] <= 0:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Token quota exceeded for today"
        )

    # Kiểm tra cuộc hội thoại tồn tại và thuộc về người dùng
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Lưu tin nhắn của người dùng
    user_message = Message(
        conversation_id=conversation_id,
        role="user",
        content=message["content"]
    )
    db.add(user_message)
    db.commit()

    # Lấy lịch sử tin nhắn của cuộc hội thoại
    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at).all()

    history = [{"role": msg.role, "content": msg.content} for msg in messages]

    # Tạo prompt từ lịch sử gần nhất
    latest_history = REFLECTION(history, lastItemsConsidereds=8)
    prompt = AITutorPrompt(history=latest_history).format()

    # Tạo assistant message trống để cập nhật sau
    assistant_message = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=""
    )
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)

    # Cập nhật thời gian cuộc hội thoại
    conversation.updated_at = datetime.now()
    db.commit()

    # Tạo generator để xử lý stream
    async def message_generator():
        full_response = ""

        async for token in generate_response_stream(prompt, current_user.id, db=db):
            full_response += token
            yield token

        # Cập nhật tin nhắn assistant khi đã hoàn thành
        assistant_message.content = full_response
        db.commit()

    return StreamingResponse(message_generator(), media_type="text/plain")


@router.get("/token-usage")
async def get_token_usage(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Lấy thông tin về việc sử dụng token của người dùng.

    Args:
        current_user (User): Người dùng hiện tại
        db (Session): Database session

    Returns:
        Dict: Thông tin về việc sử dụng token
    """
    return await check_token_quota(db, current_user.id)