"""
backend/app/services/llm_client.py
------------------
Mục đích:
- Tương tác với API LLM (Language Model) bên ngoài.
- Xử lý stream phản hồi từ LLM.
- Theo dõi việc sử dụng token để quản lý quota.

Chức năng chính:
- Tạo client OpenAI và gửi request đến API LLM.
- Ước tính số lượng token trong văn bản bằng tiktoken.
- Cung cấp hàm generate_response() để gọi API trực tiếp.
- Cung cấp hàm async generate_response_stream() để stream phản hồi và theo dõi token.
- Tự động cập nhật thống kê sử dụng token của người dùng.
"""
from openai import OpenAI
from app.config import API_KEY, GEN_API_URL, DEFAULT_MODEL, MAX_TOKENS
from typing import AsyncGenerator


def generate_response(prompt: str, model: str = DEFAULT_MODEL, max_tokens: int = MAX_TOKENS, api_key: str = API_KEY,
                      url: str = GEN_API_URL):
    """
    Gọi API LLM và trả về stream phản hồi.

    Args:
        prompt (str): Prompt đầu vào cho mô hình
        model (str): Tên mô hình sử dụng
        max_tokens (int): Số token tối đa trong phản hồi
        api_key (str): API key
        url (str): API URL

    Returns:
        stream: Stream phản hồi từ API
    """
    client = OpenAI(
        base_url=url,
        api_key=api_key
    )

    stream = client.completions.create(
        model=model,
        prompt=prompt,
        stream=True,
        max_tokens=max_tokens
    )

    return stream


async def generate_response_stream(prompt: str, model: str = DEFAULT_MODEL, max_tokens: int = MAX_TOKENS) -> \
AsyncGenerator[str, None]:
    """
    Hàm async để stream phản hồi từ LLM.

    Args:
        prompt (str): Prompt đầu vào cho mô hình
        model (str): Tên mô hình sử dụng
        max_tokens (int): Số token tối đa trong phản hồi

    Yields:
        str: Từng phần của phản hồi
    """
    stream = generate_response(prompt, model, max_tokens)

    for event in stream:
        if event.choices[0].text:
            yield event.choices[0].text