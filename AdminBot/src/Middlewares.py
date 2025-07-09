import asyncio
from tracemalloc import BaseFilter

from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Dict, Awaitable, Any

class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, rate_limit: float = 0.5):
        self.rate_limit = rate_limit
        self.cache = {}  # Хранение временных меток

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        current_time = asyncio.get_event_loop().time()

        # Проверка лимита
        if user_id in self.cache and (current_time - self.cache[user_id]) < self.rate_limit:
            # Блокируем обработку
            return None

        # Обновляем временную метку
        self.cache[user_id] = current_time

        return await handler(event, data)

