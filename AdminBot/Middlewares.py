# from aiogram import BaseMiddleware
# from aiogram.types import Message
# from aiogram import Bot, types
# from aiogram.filters import Command
# from aiogram.types import ChatMemberAdministrator
# from AdminBot.config import CHANNEL_ID
# from aiogram.types import ChatMemberOwner, ChatMemberAdministrator
# from aiogram import BaseMiddleware
# from aiogram.types import Message
#
#
# async def is_channel_admin(bot: Bot, user_id: int, channel_id: int) -> bool:
#     try:
#         member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
#         # Проверяем, является ли пользователь создателем или администратором
#         return isinstance(member, (ChatMemberOwner, ChatMemberAdministrator))
#     except Exception:
#         return False
#
#
# class AdminCheckMiddleware(BaseMiddleware):
#     async def __call__(self, handler, event: Message, data):
#         if not await is_channel_admin(event.bot, event.from_user.id, CHANNEL_ID):
#             await event.answer("🚫 У вас нет прав для выполнения этой команды!")
#             return
#         return await handler(event, data)
