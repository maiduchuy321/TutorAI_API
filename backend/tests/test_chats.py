"""
test_chat.py
------------
Mục đích:
- Kiểm thử các API endpoint của backend, đặc biệt là endpoint /chat/.
- Sử dụng thư viện như pytest và HTTPX (hoặc TestClient của FastAPI) để mô phỏng các request.

Nội dung cần có:
- Thiết lập TestClient cho FastAPI app.
- Viết các test case cho trường hợp thành công và thất bại (ví dụ: input rỗng).
- Kiểm tra kết quả trả về đúng với định dạng (model ChatResponse) và các mã lỗi phù hợp.
"""

from fastapi.testclient import TestClient
from backend.app.main import app

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_health_check():
    """ Kiểm tra API health check """
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"llm_connection": True,
                               "status": 'healthy'}


def test_chat_success():
    """ Test khi gửi request hợp lệ """
    payload = {
        "messages": [
            {"role": "user", "content": "Làm sao để in Hello World trong C++?"}
        ],
        "max_tokens": 800
    }

    response = client.post("/api/v1/chat/", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Kiểm tra dữ liệu trả về có key 'response'
    assert "response" in data
    assert isinstance(data["response"],str)
    assert len(data["response"]) > 0  # Đảm bảo có nội dung


# def test_chat_empty_input():
#     """ Test khi gửi request với messages rỗng """
#     payload = {"messages": [], "max_tokens": 800}
#
#     response = client.post("/api/message/", json=payload)
#     assert response.status_code == 400
#     data = response.json()
#     assert "detail" in data
#     assert data["detail"] == "Input messages cannot be empty"
#
#
# def test_chat_invalid_payload():
#     """ Test khi gửi request với payload không hợp lệ """
#     payload = {"wrong_key": "invalid_data"}
#
#     response = client.post("/api/message/", json=payload)
#     assert response.status_code == 422  # FastAPI sẽ tự động trả về 422 cho schema sai
#     data = response.json()
#     assert "detail" in data
