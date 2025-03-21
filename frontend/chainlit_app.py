import chainlit as cl
from backend.app.handlers.auth import oauth_callback
from backend.app.handlers.chat import start_chat, handle_message
from backend.app.config import REFLECTION
from dotenv import load_dotenv

# Nạp biến môi trường
load_dotenv()

# Gắn OAuth callback (tùy chọn, có thể bỏ qua nếu chưa cấu hình OAuth)
cl.oauth_callback(oauth_callback)

# Gắn sự kiện khởi động chat
@cl.on_chat_start
async def on_chat_start():
    await start_chat()

# Gắn sự kiện xử lý tin nhắn
@cl.on_message
async def on_message(message: cl.Message):
    await handle_message(message)

# Không cần main block vì Chainlit có CLI riêng