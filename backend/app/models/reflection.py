"""
reflection.py
-------------
Mục đích:
- Định nghĩa các lớp model liên quan đến chatbot và xử lý NLP.
- Có thể chứa các class mô hình dữ liệu, logic xử lý văn bản, hoặc tích hợp với các thư viện NLP/AI.

Nội dung cần có:
- Class định nghĩa dữ liệu input/output của chatbot.
- Các hàm hoặc class để xử lý, tiền xử lý dữ liệu trước khi gửi đến AI model.
- Nếu sử dụng ORM (SQLAlchemy, Tortoise ORM), định nghĩa các model database liên quan.
"""

"""
reflection.py
-------------
Mục đích:
- Định nghĩa các lớp model liên quan đến chatbot và xử lý NLP.
- Chứa các class định nghĩa dữ liệu input/output của chatbot.
- Tích hợp ví dụ sử dụng OpenAI API bằng cách chuyển đổi cấu trúc phản hồi của OpenAI thành đối tượng ChatResponse.

Nội dung:
- ChatRequest: chứa thông tin người dùng và văn bản đầu vào. Có phương thức tiền xử lý dữ liệu (preprocess).
- ChatResponse: chứa phản hồi từ chatbot. Có classmethod để tạo đối tượng từ kết quả trả về của OpenAI.
"""


class Reflection:
    """
    A callable class that extracts the last N items from the chat history.

    Attributes:
        None
    """

    def __call__(self, chat_history, last_items_considered=8):
        """
        Extracts the last `last_items_considered` messages from the chat history.

        Args:
            chat_history: List of chat messages.
            last_items_considered: Number of recent messages to keep.

        Returns:
            list: A truncated chat history containing only the last `last_items_considered` messages.
        """
        # Xử lý trường hợp chat_history là None hoặc rỗng
        if not chat_history:
            return []

        return chat_history[-last_items_considered:]
