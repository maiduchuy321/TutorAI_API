"""
backend/app/utils/reflection.py
------------------
Mục đích:
- Trích xuất và xử lý lịch sử hội thoại cho mô hình LLM.
- Giới hạn số lượng tin nhắn trong lịch sử để tránh vượt quá token limit.

Chức năng chính:
- Định nghĩa class Reflection với phương thức __call__ để có thể sử dụng như một hàm.
- Trích xuất N tin nhắn gần nhất từ lịch sử chat.
- Giúp tối ưu hóa độ dài của prompt gửi đến LLM.
"""


class Reflection:
    """
    Trích xuất N item gần nhất từ lịch sử chat.

    Thuộc tính:
        lastItemsConsidereds (int): Số lượng tin nhắn gần nhất cần giữ lại.
    """

    def __call__(self, chat_history, lastItemsConsidereds=8):
        """
        Trích xuất `lastItemsConsidereds` tin nhắn gần nhất từ lịch sử chat.

        Args:
            chat_history: Danh sách các tin nhắn chat.
            lastItemsConsidereds: Số lượng tin nhắn gần đây cần giữ lại.

        Returns:
            Lịch sử chat đã được cắt bớt chỉ còn `lastItemsConsidereds` tin nhắn gần nhất.
        """
        return chat_history[-lastItemsConsidereds:]