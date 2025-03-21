from datetime import datetime
import chainlit as cl
from backend.app.config import REFLECTION
from backend.app.services.llm_client import generate_response
from backend.app.utils.prompt_templates import AITutorPrompt


async def start_chat():
    """
    Khởi tạo lịch sử chat trong session.
    """
    cl.user_session.set("history", [])


async def handle_message(message: cl.Message):
    """
    Xử lý tin nhắn người dùng và trả về phản hồi từ LLM.

    Args:
        message: Tin nhắn từ người dùng.
    """
    start_time = datetime.now()
    query = message.content

    # Lấy và cập nhật lịch sử chat
    history = cl.user_session.get("history", [])
    history.append({"role": "user", "content": query})

    # Tạo prompt từ lịch sử gần nhất
    latest_history = REFLECTION(history, last_items_considered=8)
    prompt = AITutorPrompt(history=latest_history).format()

    # Tạo tin nhắn để stream
    msg = cl.Message(content="")
    await msg.send()

    # Gọi API LLM và stream phản hồi
    stream = generate_response(prompt)
    response_text = ""

    for event in stream:
        if event.choices[0].text:
            response_text += event.choices[0].text
            await msg.stream_token(event.choices[0].text)

    # Cập nhật lịch sử với phản hồi
    history.append({"role": "Assistant", "content": response_text})
    cl.user_session.set("history", history)

    # Tính thời gian xử lý và cập nhật tin nhắn
    end_time = datetime.now()
    processing_time = (end_time - start_time).total_seconds()
    final_content = f"{response_text} (⏱ {processing_time:.3f}s)"
    msg.content = final_content
    await msg.update()