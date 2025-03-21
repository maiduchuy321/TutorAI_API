import chainlit as cl
from typing import Dict, Optional


def oauth_callback(provider_id: str, token: str, raw_user_data: Dict[str, str], default_user: cl.User) -> Optional[
    cl.User]:
    """
    Xác thực OAuth với Google.

    Args:
        provider_id: ID của nhà cung cấp OAuth.
        token: Token xác thực.
        raw_user_data: Thông tin người dùng từ nhà cung cấp.
        default_user: Đối tượng người dùng mặc định.

    Returns:
        cl.User hoặc None: Đối tượng người dùng nếu xác thực thành công, None nếu không.
    """
    if provider_id == "google":
        return cl.User(
            identifier=raw_user_data["email"],
            metadata={"provider": "google", "name": raw_user_data.get("name", "")}
        )
    return None