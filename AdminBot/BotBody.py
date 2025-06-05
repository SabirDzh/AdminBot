import random
import re
from aiogram import *
import asyncio
import os
from aiogram.types import *
from config import TOKEN_API
from aiogram.filters import *
from aiogram.utils.keyboard import *
from random import *
from aiogram.fsm.context import *
from aiogram.fsm.state import *
from aiogram.filters.callback_data import *
from aiogram.utils import *
from aiogram.exceptions import *
import hashlib
import logging
from aiogram.enums import *
from aiogram.client.default import *
from aiogram.utils.formatting import Text, Bold
from datetime import datetime, date
from AdminBot.Keyboards import *
from aiogram.utils.media_group import MediaGroupBuilder
from aiogram.enums.chat_member_status import ChatMemberStatus
from aiogram.enums.parse_mode import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramBadRequest
from contextlib import suppress
from datetime import datetime, timedelta
import asyncpg

command_router = Router()
message_router = Router()

dp = Dispatcher()

HELP_COMMAND = '''
<b>/start</b> - <em>запуск бота</em>
<b>/help</b> - <em>список всех команд</em>
<b>/status</b> - <em>узнать статус</em>
<b>/rules</b> - <em>правила группы</em>
<b>/id</b> - <em>ваш id</em>
<b>/ban</b> - <em>забанить</em>
<b>/mute</b> - <em>предупреждение</em>
<b>/unmute</b> - <em>размутить</em>
<b>/unban</b> - <em>разбанить</em>
<b>/warn</b> - <em>предупреждение</em>
<b>/unwarn</b> - <em>убрать предупреждение</em>
<b>/stat</b> - <em>статистика за неделю</em>
<b>/activ</b> - <em>самые активные</em>
<b>/total_warn</b> - <em>больше всего предупреждений</em>
<b>/poll</b> - <em>создать опрос</em>
<b>/language</b> - <em>выбор языка</em>
'''

RULES_COMMAND = '''
<b>Правила чата:</b>
1) Оскорбление участников, запрещено 
2) Обсуждение политики, запрещено 
3) Экстримальный контент, запрещено
4) Контент 18+, запрещен 
5) Вредоносные ссылки, запрещено 
6) Спам, запрещено
7) Реклама без согласия администратора, запрещено

<b>ВАЖНОЕ!</b>
Действие администратора не подлежит обсуждению!
Администратор решает какое наказание выбрать за нарушение правил!
'''

HELP_PRIVATE_COMMAND = '''
<b>/id</b> - <em>узнать свой id</em>
<b>/language</b> - <em>язык бота</em>
<b>/poll</b> - <em>создать опрос</em
'''


class Reg(StatesGroup):
    user_id = State()
    chat_id = State()
    correct_answer = State()
    join_date = State()
    captcha_message_id = State()


KEEP_DAYS = 7
CREATE_TABLE = """
               CREATE TABLE IF NOT EXISTS message
               (
                   user_id
                   BIGINT
                   NOT
                   NULL,
                   message_date
                   DATE
                   NOT
                   NULL,
                   message_count
                   INT
                   NOT
                   NULL
                   DEFAULT
                   0,
                   PRIMARY
                   KEY
               (
                   user_id,
                   message_date
               )
                   ); \
               """


async def init_db(pool: asyncpg.Pool):
    async with pool.acquire() as conn:
        await conn.execute(CREATE_TABLE)


@command_router.message(Command("start"))
async def start_cms(message: Message):
    if message.chat.type == "private":
        await message.answer(
            f"Здравствуйте, <b>{message.from_user.full_name}</b>, этот бот предназначен для работы с группами!",
            parse_mode="HTML"
        )
        return
    await message.answer(
        f"<b>{message.from_user.full_name}</b>, рад вас видеть!\n\nИспользуйте <b>/help</b> для просмотра всех команд.",
        parse_mode="HTML")


@command_router.message(Command("help"))
async def help_cmd(message: Message):
    if message.chat.type == "private":
        await message.answer(text=HELP_PRIVATE_COMMAND,
                             parse_mode="HTML")
        return
    await message.answer(text=HELP_COMMAND,
                         parse_mode="HTML")


@message_router.message(F.chat.type.in_({"group", "supergroup"}))
async def count_message(message: Message, pool: asyncpg.Pool):
    user_id = message.from_user.id
    today = date.today()

    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                """
                INSERT INTO message(user_id, message_date, message_count)
                VALUES ($1, $2, 1) ON CONFLICT (user_id, message_date)
                DO
                UPDATE SET message_count = message.message_count + 1
                """,
                user_id, today
            )

            await conn.execute(
                """
                DELETE
                FROM message
                WHERE message_date < $1;
                """,
                today - timedelta(days=KEEP_DAYS)
            )


@command_router.message(F.chat.type != "private", Command("rules"))
async def rules_cmd(message: Message):
    await message.answer(text=RULES_COMMAND,
                         parse_mode="HTML")


@command_router.message(Command("id"))
async def id_cmd(message: Message):
    await message.reply(f"Ваш id: {message.from_user.id}")


async def is_admin(message: Message, bot: Bot) -> bool:
    try:
        user_member = await bot.get_chat_member(message.chat.id, message.from_user.id)
        return isinstance(user_member, (ChatMemberAdministrator, ChatMemberOwner))
    except TelegramBadRequest:
        return False


def parse_time(time_str: str | None) -> datetime | None:
    if not time_str:
        return None

    pattern = r"^(\d+)([hdw])$"
    match = re.match(pattern, time_str.lower())
    if not match:
        return None

    value = int(match.group(1))
    unit = match.group(2)

    now = datetime.now()

    if unit == "0":
        return None

    time_units = {
        'h': timedelta(hours=value),
        'd': timedelta(days=value),
        'w': timedelta(weeks=value)
    }

    return now + time_units.get(unit, timedelta(0)) if unit in time_units else None


async def is_check(message: Message):
    reply = message.reply_to_message
    usr = message.from_user.id
    try:
        if not reply or reply.from_user.is_bot or not reply.from_user.id != usr:
            return False
        return True
    except TelegramBadRequest:
        return False


@command_router.message(F.chat.type != "private", Command("mute"))
async def mute_cmd(message: Message, command: CommandObject, bot: Bot):
    if not await is_check(message):
        await message.reply("Используйте эту команду в ответ на сообщение пользователя")
        return

    if not await is_admin(message, bot):
        await message.reply("У вас нет прав администратора!")
        return

    mute_time = parse_time(command.args)
    if not mute_time:
        await message.reply("Неверный формат времени. Пример: /mute 1h")
        return

    target_user = message.reply_to_message.from_user
    mention = target_user.mention_html(target_user.first_name)

    try:
        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=target_user.id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=mute_time
        )
        await message.answer(
            f"Пользователь <b>{mention}</b> замучен до <b>{mute_time.strftime('%H:%M:%S %d.%m.%Y')}</b>.",
            parse_mode="HTML")
    except TelegramBadRequest as e:
        await message.reply(f"Ошибка: {e}")


@command_router.message(F.chat.type != "private", Command("unmute"))
async def unmute_cmd(message: Message, bot: Bot):
    reply_message = message.reply_to_message

    if not await is_check(message):
        await message.reply("Используйте эту команду в ответ на сообщение")
        return

    if not await is_admin(message, bot):
        await message.reply("У вас нет прав администратора")
        return

    mention = reply_message.from_user.mention_html(reply_message.from_user.first_name)

    await bot.restrict_chat_member(chat_id=message.chat.id, user_id=reply_message.from_user.id,
                                   permissions=ChatPermissions(can_send_messages=True,
                                                               can_send_other_messages=True))
    await message.answer(f"Все ограничения с пользователя <b>{mention}</b> были сняты",
                         parse_mode="HTML")


@command_router.message(F.chat.type != "private", Command("status"))
async def status_cmd(message: Message, bot: Bot):
    member = await bot.get_chat_member(chat_id=message.chat.id, user_id=message.from_user.id)
    status = member.status
    user_name = message.from_user.full_name

    if status == "creator":
        full_status = "<b>Создатель</b>"
    elif status == "administrator":
        full_status = "<b>Администратор</b>"
    else:
        full_status = "<b>Обычный пользователь</b>"
    await message.answer(text=f"Статус пользователя {user_name}: {full_status}",
                         parse_mode="HTML")


class Users:
    def __init__(self, message, bot):
        self.message = message
        self.bot = bot

    async def _very_private_method(self):
        member = await self.bot.get_chat_member(chat_id=self.message.chat.id, user_id=self.message.from_user.id)
        return member

    async def get_info_users(self):
        await self._very_private_method()
        status = (await self._very_private_method()).status


@command_router.message(F.chat.type != "private", Command("ban"))
async def ban_cmd(message: Message, bot: Bot, pool: asyncpg.Pool):
    member = await bot.get_chat_member(chat_id=message.chat.id, user_id=message.from_user.id)
    status = member.status

    member_reply_user = await bot.get_chat_member(chat_id=message.chat.id,
                                                  user_id=message.reply_to_message.from_user.id)
    status_user = member_reply_user.status

    # us = Users(message, bot)    | тестирование
    # await us.get_info_users()

    if not await is_check(message):
        await message.reply("Используйте эту команду в ответ на сообщение пользователя")
        return

    target_user = message.reply_to_message.from_user
    mention = target_user.mention_html(target_user.first_name)

    if not await is_admin(message, bot):
        await message.reply("У вас нет прав администратора")
        return

    if status == "creator" and status_user != ChatMemberStatus.KICKED:
        await bot.ban_chat_member(chat_id=message.chat.id, user_id=target_user.id)
        await message.answer(f"Пользователь <b>{mention}</b> забанен.",
                             parse_mode="HTML")
        return

    elif status == "administrator" and status_user != "creator" and status_user != ChatMemberStatus.KICKED:
        await bot.ban_chat_member(chat_id=message.chat.id, user_id=target_user.id)
        await message.answer(f"Пользователь <b>{mention}</b> забанен.",
                             parse_mode="HTML")
        async with (pool.acquire() as conn):
            await conn.execut(
                """ 
                insert into ban 
                """
            )

        return
    await message.reply("Пользователь выше по званию")


@command_router.message(F.chat.type != "private", Command("unban"))
async def unban_cmd(message: Message, bot: Bot):
    member = await bot.get_chat_member(chat_id=message.chat.id, user_id=message.from_user.id)
    status = member.status

    member_reply_user = await bot.get_chat_member(chat_id=message.chat.id,
                                                  user_id=message.reply_to_message.from_user.id)
    status_user = member_reply_user.status

    if not await is_check(message):
        await message.reply("Используйте эту команду в ответ на сообщение пользователя")
        return

    target_user = message.reply_to_message.from_user
    mention = target_user.mention_html(target_user.first_name)

    if not await is_admin(message, bot):
        await message.reply("У вас нет прав администратора")
        return

    if status == "administrator":
        if status_user == "administrator" and status_user == ChatMemberStatus.KICKED:
            await message.reply("Вы не можете разбанить равного по званию")
            return
        elif status_user != ChatMemberStatus.KICKED:
            await message.reply("Пользователь не забанен")
            return
        await bot.unban_chat_member(chat_id=message.chat.id, user_id=target_user.id, only_if_banned=True)
        await message.answer(f"Пользователь <b>{mention}</b> разбанен",
                             parse_mode="HTML")

    elif status == "creator" and status_user == ChatMemberStatus.KICKED:
        await bot.unban_chat_member(chat_id=message.chat.id, user_id=target_user.id)
        await message.answer(f"Пользователь <b>{mention}</b> разбанен",
                             parse_mode="HTML")

    await message.reply("Пользователь не забанен")
    return


@command_router.chat_member(ChatMemberUpdatedFilter(member_status_changed=JOIN_TRANSITION))
async def capcha(event: ChatMemberUpdated, bot: Bot, state: FSMContext):
    user = event.new_chat_member.user

    try:
        sent_message = await bot.send_message(
            chat_id=user.id,
            reply_markup=await button_for_capcha()
        )

        await state.update_data(capcha_message_id=sent_message.message_id)

        await bot.restrict_chat_member(
            chat_id=event.chat.id,
            user_id=user.id,
            permissions=ChatPermissions(can_send_messages=False)
        )

    except Exception as e:
        await bot.ban_chat_member(event.chat.id, user.id)
        await event.answer(f"Не удалось отправить капчу. Пользователь {user.mention_html()} забанен.")


# @router.message(F.text)
# async def check_answer(message: Message, bot: Bot, state: FSMContext):
#     data = await state.get_data()
#
#     try:
#         if message.from_user.id != data['user_id']:
#             return
#
#         if int(message.text) == data['correct_answer']:
#             # Восстанавливаем права
#             await bot.restrict_chat_member(
#                 chat_id=data['chat_id'],
#                 user_id=data['user_id'],
#                 permissions=ChatPermissions.all()
#             )
#             await message.answer("✅ Верно! Добро пожаловать в чат!")
#         else:
#             await message.answer("❌ Неверно! Попробуйте ещё раз.")
#
#     except (KeyError, ValueError):
#         await message.answer("⚠️ Произошла ошибка. Обратитесь к администратору.")
#     finally:
#         await state.clear()

# чем отличается bot.send_message от message.answer ?

@command_router.message(F.chat.type != "private", Command("warn"))
async def warn_cmd(message: Message, bot: Bot, pool: asyncpg.Pool):
    message_reply = message.reply_to_message.from_user

    if not await is_check(message):
        await message.reply("Используйте эту команду в ответ на сообщение пользователя")
        return
    elif not await is_admin(message, bot):
        await message.reply("У вас нет прав администратора")
        return

    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO warn (user_id, warn_count, total_warn)
            VALUES ($1, 1, 1) ON CONFLICT (user_id) 
            DO
            UPDATE SET
                warn_count = warn.warn_count + 1,
                total_warn = warn.total_warn + 1
            """,
            message_reply.id
        )

        warn_count = await conn.fetchval(
            "select warn_count from warn where user_id = $1",
            message_reply.id
        )

        is_banned = await conn.fetchval(
            "select ban from warn where user_id = $1",
            message_reply.id
        )

    chat = (await bot.get_chat(message.chat.id)).title
    if is_banned:
        try:
            await bot.ban_chat_member(user_id=message_reply.id, chat_id=message.chat.id)
            await bot.send_message(message_reply.id,
                                   f"{message_reply.mention_html()} был заблокирован за нарушения в группе <b>{chat}</b>",
                                   parse_mode="HTML")
            return
        except TelegramForbiddenError:
            await bot.send_message(message.chat.id,
                                   f"{message_reply.mention_html()} был заблокирован за нарушения в группе <b>{chat}</b>",
                                   parse_mode="HTML")
            return

    await message.answer(f"⚠️ Пользователь {message_reply.mention_html()} получил предупреждение.\n"
                         f"Текущее количество: {warn_count}/3",
                         parse_mode="HTML")


@command_router.message(Command("stat"))
async def cmd_stat(message: Message, pool: asyncpg.Pool):
    user_id = message.from_user.id
    today = date.today()

    dates = [(today - timedelta(days=i)).strftime("%d.%m.%y") for i in range(6, -1, -1)]

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT message_date, message_count
            FROM message
            WHERE user_id = $1
              AND message_date >= $2
            ORDER BY message_date;
            """,
            user_id,
            today - timedelta(days=KEEP_DAYS),
        )

    stats_dict = {
        row['message_date'].strftime("%d.%m.%y"): row['message_count']
        for row in rows
    }
    result = [f"{datee} — {stats_dict.get(datee, 0)} сообщений" for datee in dates]

    await message.answer("\n".join(reversed(result)))
