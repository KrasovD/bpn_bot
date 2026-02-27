from aiogram.filters import BaseFilter
from aiogram.types import Message

from app.db import get_user

class AuthorizedOnly(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return get_user(message.chat.id) is not None

class AdminOnly(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        u = get_user(message.chat.id)
        return bool(u and u["role"] == "admin")