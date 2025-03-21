from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Tạm thời bỏ phần Chainlit vì chưa cấu hình OAuth
import chainlit as cl
from ..app.handlers.auth import oauth_callback
from ..app.handlers.chat import start_chat, handle_message

from ..app.routes.chat_routes import router as chat_router

# Khởi tạo FastAPI app
app = FastAPI(
    title="AI Tutor Chatbot API",
    description="API cho ứng dụng AI Tutor Chatbot",
    version="0.0.1",
)

# Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Trong môi trường production, hãy giới hạn các origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đăng ký router
app.include_router(chat_router, prefix="/api/v1", tags=["chat"])

# Bỏ phần Chainlit vì chưa cấu hình OAuth
# cl.oauth_callback(oauth_callback)
# cl.on_chat_start(start_chat)
# cl.on_message(handle_message)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8001, reload=True)