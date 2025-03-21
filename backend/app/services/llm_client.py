"""
llm_client.py
----------
Mục đích:
- Xử lý logic chính của chatbot: nhận đầu vào từ API, xử lý (gọi AI model, xử lý NLP, ...) và trả về kết quả.
- Tách biệt phần xử lý logic khỏi API endpoint để code rõ ràng, dễ kiểm thử.

Nội dung cần có:
- Hàm generate_response() để gọi các API AI (ví dụ: OpenAI GPT) và xử lý phản hồi.
- Các hàm hỗ trợ xử lý văn bản như tiền xử lý, hậu xử lý nếu cần.
- Xử lý các lỗi có thể xảy ra khi gọi model AI.
"""

from openai import OpenAI
from backend.app.config import API_KEY, GEN_API_URL, DEFAULT_MODEL, MAX_TOKENS


def generate_response(prompt: str, model: str = DEFAULT_MODEL, max_tokens: int = MAX_TOKENS, api_key: str = API_KEY,
                      url: str = GEN_API_URL):
    """
    Tạo phản hồi từ LLM dựa trên prompt.

    Args:
        prompt: Chuỗi prompt để gửi đến LLM
        model: Tên mô hình LLM (mặc định: LLama-3.3-70B-Instruct)
        max_tokens: Số token tối đa cho phản hồi
        api_key: API key để truy cập dịch vụ LLM
        url: URL của API LLM

    Returns:
        stream: Stream phản hồi từ LLM
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


def health_check():
    """
    Kiểm tra kết nối với API LLM.

    Returns:
        bool: True nếu kết nối được thiết lập, False nếu không
    """
    try:
        client = OpenAI(
            base_url=GEN_API_URL,
            api_key=API_KEY
        )
        # Gửi prompt ngắn để kiểm tra kết nối
        client.completions.create(
            model=DEFAULT_MODEL,
            prompt="Hello",
            max_tokens=5
        )
        return True
    except Exception:
        return False