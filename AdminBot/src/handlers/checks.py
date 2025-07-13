from aiogram import *
from aiogram.enums import *
from aiogram.handlers import callback_query
from aiogram.types import *
from aiogram.filters import *
from aiogram.exceptions import *
from aiogram.enums.chat_member_status import *
from aiogram.exceptions import TelegramBadRequest
import logging


async def is_check_all_rules(status=ChatMemberStatus | None, reply_user_status=Any | None, reply_user=Any | None,
                             bot_member=Any | None) -> int:
    if status not in {ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR}:
        return 1
    elif not bot_member.can_restrict_members:
        return 4
    elif reply_user_status == ChatMemberStatus.CREATOR:
        return 2
    elif reply_user_status == ChatMemberStatus.ADMINISTRATOR:
        if status != ChatMemberStatus.CREATOR:
            return 3
    elif reply_user.is_bot:
        return 5
    elif reply_user_status == ChatMemberStatus.KICKED:
        return 7
    elif reply_user_status == ChatMemberStatus.LEFT:
        return 8
    return 6


ErrorBan: dict = {1: "У вас нет прав", 2: "Пользователь выше по званию", 3: "Пользователь равен по званию",
                  4: "У бота недостаточно прав", 5: "Нельзя кикнуть/забанить бота", 6: True, 7: "Пользователь забанен",
                  8: "Пользователь покинул группу", 9: "Пользователь уже забанен", 10: "Пользователь не забанен"}


# В РАЗРАБОТКЕ
class AllCheck:
    def __init__(self, user: ChatMemberStatus, target_user: ChatMemberStatus, bot_member: Any, reply_user: User):
        self.user = user
        self.target_user = target_user
        self.bot_member = bot_member
        self.reply_user = reply_user
        self.is_true_check = True

    async def is_status(self, message: Message):
        if self.user not in [ChatMemberStatus.CREATOR, ChatMemberStatus.ADMINISTRATOR]:
            await message.reply(text="У вас нет прав")
            self.is_true_check = False
            raise message.reply(text="Тест")

    async def is_member_bot(self, message: Message):
        if not self.bot_member.can_restrict_members:
            await message.reply(text="У бота недостаточно прав")
            self.is_true_check = False
            raise message.reply(text="Тест")

    async def is_can_ban(self, message: Message):
        if self.target_user == ChatMemberStatus.ADMINISTRATOR:
            if self.user != ChatMemberStatus.CREATOR:
                await message.reply(text="Пользователь равен по званию",)
                self.is_true_check = False
                raise message.reply(text="Тест")

        elif self.target_user == ChatMemberStatus.CREATOR:
            await message.reply(text="Пользователь является создателем")
            self.is_true_check = False
            raise message.reply(text="Тест")

        elif self.target_user == ChatMemberStatus.LEFT:
            await message.reply(text="Пользователь/Бот не состоит в группе группу")
            self.is_true_check = False
            raise message.reply(text="Тест")

    async def is_unban(self, message: Message):
        if self.target_user != ChatMemberStatus.KICKED and not self.reply_user.is_bot:
            await message.reply(text="Пользователь не забанен")
            self.is_true_check = False
            raise message.reply(text="Тест")

        elif self.target_user != ChatMemberStatus.KICKED and self.reply_user.is_bot:
            await message.reply(text="Бот не забанен")
            self.is_true_check = False
            raise message.reply(text="Тест")

    async def is_ban(self, message: Message):
        if self.target_user == ChatMemberStatus.KICKED and not self.reply_user.is_bot:
            await message.reply(text="Пользователь уже забанен")
            self.is_true_check = False
            raise message.reply(text="Тест")
        elif not self.bot_member.can_restrict_members and self.reply_user.is_bot:
            await message.reply(text="Бот уже забанен")
            self.is_true_check = False
            raise message.reply(text="Тест")
        elif self.reply_user.is_bot:
            await message.reply(text="Нельзя забанить/кикнуть бота")
            self.is_true_check = False
            raise message.reply(text="Тест")

    async def result_check(self):
        return self.is_true_check
