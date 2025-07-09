from aiogram import *
from aiogram.enums import ParseMode
from aiogram.handlers import callback_query
from aiogram.types import *
from aiogram.filters import *
from aiogram.exceptions import *
from aiogram.enums.chat_member_status import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest
import logging

async def is_check_all_rules(status=Any, reply_user_status=Any, reply_user=Any, bot_member=Any):
    if status not in {"administrator", "creator"}:
        return 1
    elif not bot_member.can_restrict_members:
        return 4
    elif reply_user_status == "creator":
        return 2
    elif reply_user_status == "administrator":
        if status != "creator":
            return 3
    elif reply_user.is_bot:
        return 5
    elif reply_user_status == "kicked":
        return 7
    elif reply_user_status == "left":
        return 8
    return 6
