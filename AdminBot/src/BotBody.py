import re
import asyncio
import token
from sys import thread_info

from aiogram import *
from aiogram.enums import ParseMode
from aiogram.handlers import callback_query
from aiogram.types import *
from aiogram.filters import *
from aiogram.fsm.context import *
from aiogram.fsm.state import *
from aiogram.exceptions import *
from datetime import date
from AdminBot.src.Keyboards import *
from aiogram.enums.chat_member_status import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest
from datetime import datetime, timedelta
import asyncpg
from AdminBot.src.Database.models import *
from Middlewares import *
from telethon.sync import TelegramClient
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsRecent
from AdminBot.src.handlers.checks import *
import logging
from AdminBot.src.states.user_states import *
import html

command_router = Router()
message_router = Router()

dp = Dispatcher()
command_router.message.middleware(ThrottlingMiddleware(rate_limit=0))

# client = TelegramClient("denote_all", API_ID, API_HASH)
# client.start()

HELP_COMMAND = '''
<b>/status</b> - <em>узнать статус</em>
<b>/rules</b> - <em>правила группы</em>
<b>/id</b> - <em>ваш id</em>
<b>/ban</b> - <em>забанить</em>
<b>/mute</b> - <em>предупреждение</em>
<b>/unmute</b> - <em>размутить</em>
<b>/unban</b> - <em>разбанить</em>
<b>/warn</b> - <em>предупреждение</em>
<b>/unwarn</b> - <em>(НЕ ГОТОВА)</em>
<b>/stat</b> - <em>статистика за неделю</em>
<b>/activ</b> - <em>самые активные</em>
<b>/total_warn</b> - <em>больше всего предупреждений</em>
<b>/chatID</b> - <em>id группы</em>
<b>/all</b> - <em>упомянуть всех</em>
<b>/language</b> - <em>выбор языка</em>
<b>/kick</b> - <em>выгнать пользователя</em>
<b>/captcha</b> - <em>настройка капчи</em>
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
<b>/poll</b> - <em>создать опрос</em>
<b>/helps имя команды</b> - <em>описание команды</em>
<b>/report описание ошибки</b> - <em>сообщить про ошибку</em>
<b>/support</b> - <em>поддержка</em>
'''

URL_PATTERN = re.compile(r'https://t\.me/\+[\w]+')


class Reg(StatesGroup):
    user_id = State()
    chat_id = State()
    correct_answer = State()
    join_date = State()
    captcha_message_id = State()
    new_rule = State()
    new_user_in_group_id = State()
    is_capcha = State()


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
async def rules_cmd(message: Message, pool: asyncpg.Pool):
    async with pool.acquire() as conn:
        result = await conn.fetchval(
            "SELECT rules FROM group_rules WHERE group_id = $1",
            message.chat.id
        )

        if not result:
            result = RULES_COMMAND
            await conn.execute(
                "INSERT INTO group_rules(group_id, rules) VALUES ($1, $2)",
                message.chat.id,
                result
            )

    await message.answer(
        text=result,
        parse_mode="HTML",
        reply_markup=edit_rule_group()
    )


@command_router.callback_query(F.data == "edit_rule_group")
async def edit_rule_group_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Reg.new_rule)
    await callback.message.edit_text(text="⬇️ Введите новые правила ⬇️")
    await callback.answer()


@command_router.message(StateFilter(Reg.new_rule))
async def reg_new_rule_for_group(message: Message, state: FSMContext, pool: asyncpg.Pool):
    await state.update_data(new_rule=message.text)
    data = await state.get_data()

    try:
        async with pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    """
                    update group_rules
                    set rules = $2
                    where group_id = $1
                    """,
                    message.chat.id,
                    data["new_rule"]
                )
    except Exception:
        await message.reply(text="<b>Вы ввели слишком мало символов!</b>\n\nМинимальное количество символов 50",
                            parse_mode="HTML")
        return

    sent_message = await message.answer(text="Правила обновлены!")

    await asyncio.create_task(delayed_delete(sent_message, 2))


async def delayed_delete(message: Message, delay: int):
    await asyncio.sleep(delay)
    await message.delete()


@command_router.message(Command("id"))
async def id_cmd(message: Message):
    await message.reply(f"Ваш id: {message.from_user.id}")


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


@command_router.message(F.chat.type != "private", Command("mute"))
async def mute_cmd(message: Message, command: CommandObject, bot: Bot):
    if not message.reply_to_message:
        await message.reply("❗ Используйте эту команду в ответ на сообщение пользователя")
        return

    target_user = await bot.get_chat_member(chat_id=message.chat.id,
                                            user_id=message.reply_to_message.from_user.id)
    user = await bot.get_chat_member(chat_id=message.chat.id,
                                     user_id=message.from_user.id)
    bot_member = await bot.get_chat_member(chat_id=message.chat.id,
                                           user_id=bot.id)
    reply_member = message.reply_to_message.from_user

    check = AllCheck(user.status, target_user.status, bot_member, reply_member)

    mute_time = parse_time(command.args)
    if not mute_time:
        await message.reply("Неверный формат времени. Пример: /mute 1h")
        return

    mention = reply_member.mention_html(reply_member.username)

    await check.is_status(message)
    await check.is_member_bot(message)
    await check.is_can_ban(message)
    result = await check.result_check()

    if result == False:
        return

    try:
        if reply_member.is_bot:
            return await message.reply(text="Бота нельзя замутить")

        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=reply_member.id,
            permissions=ChatPermissions(can_send_messages=False, can_send_media_messages=False, can_send_polls=False,
                                        can_send_audios=False, can_send_documents=False, can_send_stickers=False,
                                        can_send_gifs=False, can_add_web_page_previews=False),
            until_date=mute_time
        )
        await message.answer(
            f"Пользователь <b>{mention}</b> замучен до <b>{mute_time.strftime('%H:%M:%S %d.%m.%Y')}</b>.",
            parse_mode="HTML")
    except TelegramBadRequest as e:
        await message.reply(f"Ошибка: {e}")


@command_router.message(F.chat.type != "private", Command("unmute"))
async def unmute_cmd(message: Message, bot: Bot):
    if not message.reply_to_message:
        await message.reply("❗ Используйте эту команду в ответ на сообщение пользователя")
        return

    target_user = await bot.get_chat_member(chat_id=message.chat.id,
                                            user_id=message.reply_to_message.from_user.id)
    user = await bot.get_chat_member(chat_id=message.chat.id,
                                     user_id=message.from_user.id)
    bot_member = await bot.get_chat_member(chat_id=message.chat.id,
                                           user_id=bot.id)
    reply_member = message.reply_to_message.from_user

    check = AllCheck(user.status, target_user.status, bot_member, reply_member)
    await check.is_status(message)
    await check.is_member_bot(message)
    await check.is_can_ban(message)
    result = await check.result_check()

    if result == False:
        return

    mention = reply_member.mention_html(reply_member.username)

    if reply_member.is_bot:
        return await message.reply(text="Бота нельзя размутить")

    await bot.restrict_chat_member(chat_id=message.chat.id, user_id=reply_member.id,
                                   permissions=ChatPermissions(can_send_messages=False, can_send_media_messages=False,
                                                               can_send_polls=False,
                                                               can_send_audios=False, can_send_documents=False,
                                                               can_send_stickers=False,
                                                               can_send_gifs=False, can_add_web_page_previews=False))
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


@command_router.message(F.chat.type != "private", F.text.startswith("/ban"))
async def ban_cmd(message: Message, bot: Bot, pool: asyncpg.Pool):
    if not message.reply_to_message:
        await message.reply("❗ Используйте эту команду в ответ на сообщение пользователя")
        return

    target_user = await bot.get_chat_member(chat_id=message.chat.id,
                                            user_id=message.reply_to_message.from_user.id)
    user = await bot.get_chat_member(chat_id=message.chat.id,
                                     user_id=message.from_user.id)
    bot_member = await bot.get_chat_member(chat_id=message.chat.id,
                                           user_id=bot.id)
    reply_member = message.reply_to_message.from_user

    check = AllCheck(user.status, target_user.status, bot_member, reply_member)
    await check.is_status(message)
    await check.is_member_bot(message)
    await check.is_can_ban(message)
    await check.is_ban(message)
    result = await check.result_check()

    if result == False:
        return

    reason = " ".join(message.text.split(" ")[1:]) or "Без причины"

    try:
        await bot.ban_chat_member(
            chat_id=message.chat.id,
            user_id=message.reply_to_message.from_user.id,
            revoke_messages=True
        )

        mention_admin = message.from_user.mention_html(message.from_user.username)
        mention_target = reply_member.mention_html(reply_member.username)

        response = (
            f"🚷 Пользователь {mention_target} забанен.\n"
            f"👮 Забанил: {mention_admin}\n"
            f"📝 Причина: {reason}"
        )

        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO ban_user_adm_bot (
                    chat_id, 
                    user_id, 
                    reason, 
                    last_ban, 
                    is_ban, 
                    banned_by
                ) VALUES ($1, $2, $3, $4, $5, $6)
                """,
                message.chat.id,
                reply_member.id,
                reason,
                datetime.now(),
                True,
                message.from_user.id
            )
        await message.reply(response, parse_mode="HTML")

    except Exception as e:
        await message.reply(f"❌ Ошибка при выполнении команды: {str(e)}")


@command_router.message(F.chat.type != "private", Command("unban"))
async def unban_cmd(message: Message, bot: Bot, pool: asyncpg.Pool):
    if not message.reply_to_message:
        await message.reply("❗ Используйте эту команду в ответ на сообщение пользователя")
        return

    target_user = await bot.get_chat_member(chat_id=message.chat.id,
                                            user_id=message.reply_to_message.from_user.id)
    user = await bot.get_chat_member(chat_id=message.chat.id,
                                     user_id=message.from_user.id)
    bot_member = await bot.get_chat_member(chat_id=message.chat.id,
                                           user_id=bot.id)
    reply_member = message.reply_to_message.from_user

    check = AllCheck(user.status, target_user.status, bot_member, reply_member)
    await check.is_status(message)
    await check.is_member_bot(message)
    await check.is_can_ban(message)
    await check.is_unban(message)

    result = await check.result_check()
    if result == False:
        return

    try:
        # Выполняем разбан
        await bot.unban_chat_member(
            chat_id=message.chat.id,
            user_id=message.reply_to_message.from_user.id,
            only_if_banned=True
        )

        # Обновляем статус в базе данных
        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE ban_user_adm_bot SET is_ban = FALSE "
                "WHERE chat_id = $1 AND user_id = $2",
                message.chat.id, reply_member.id
            )

        # Формируем сообщение об успехе
        mention = reply_member.mention_html(reply_member.username)
        await message.answer(f"🔓 Пользователь <b>{mention}</b> разбанен", parse_mode="HTML")

    except Exception as e:
        await message.reply(f"❌ Произошла ошибка при разбане пользователя: {str(e)}")


@command_router.message(Command("captcha"))
async def cmd_setting_capcha(message: Message, bot: Bot, pool: asyncpg.Pool):
    try:
        member = await bot.get_chat_member(chat_id=message.chat.id,
                                           user_id=message.from_user.id)
        status = member.status

        if status not in {ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR}:
            return await message.reply("Пользователь не имеет прав администратора")

        bot_member = await bot.get_chat_member(chat_id=message.chat.id,
                                               user_id=bot.id)
        if not bot_member.can_restrict_members:
            return await message.reply("Бот не имеет прав для ограничений пользователей")

        async with pool.acquire() as conn:
            info_captcha = await conn.fetchrow(
                """
                select status, text_capcha
                from setting_capcha
                where chat_id = $1
                """,
                message.chat.id
            )

        if info_captcha is None:
            status_flag = True
            text = "Добро пожаловать! Пройдите проверку"
        else:
            status_flag = info_captcha["status"]
            text = html.escape(info_captcha["text_capcha"]) or "Добро пожаловать! Пройдите проверку"

        status = "Включена" if status_flag else "Выключена"

        if status == "Включена":
            keyboard = await keyboard_menu_setting_capcha()
        elif status == "Выключена":
            keyboard = await keyboard_menu_setting_capcha_two()

        await message.answer(f"Меню настройки капчи\n\nСтатус: <b>{status}</b>\n\nПриветствие: {text}",
                             reply_markup=keyboard,
                             parse_mode="HTML")

    except Exception as e:

        await message.reply(text=f"Ошибка: {e}")


@command_router.callback_query(F.data == "on_captcha")
async def on_capcha(callback: CallbackQuery, pool: asyncpg.Pool):
    async with pool.acquire() as conn:
        await conn.execute(
            """
            insert into setting_capcha(status, chat_id)
            values (FALSE, $1) on conflict (chat_id)
            do
            update set status = FALSE
            where setting_capcha.status is distinct
            from FALSE""",
            callback.message.chat.id
        )

        info_captcha = await conn.fetchrow(
            """
            select status, text_capcha
            from setting_capcha
            where chat_id = $1
            """,
            callback.message.chat.id
        )

    if info_captcha is None:
        text = "Добро пожаловать! Пройдите проверку"
    else:
        text = html.escape(info_captcha["text_capcha"]) or "Добро пожаловать! Пройдите проверку"

    await callback.message.edit_text(f"Меню настройки капчи\n\nСтатус: <b>Выключена</b>\n\nПриветствие: {text}",
                                     reply_markup=await keyboard_menu_setting_capcha_two(),
                                     parse_mode="HTML")
    await callback.answer()


@command_router.callback_query(F.data == "off_captcha")
async def off_capcha(callback: CallbackQuery, pool: asyncpg.Pool):
    async with pool.acquire() as conn:
        await conn.execute(
            """
            insert into setting_capcha(status, chat_id)
            values (TRUE, $1) on conflict (chat_id)
            do
            update set status = TRUE
            where setting_capcha.status is distinct
            from TRUE""",
            callback.message.chat.id
        )

        info_captcha = await conn.fetchrow(
            """
            select status, text_capcha
            from setting_capcha
            where chat_id = $1
            """,
            callback.message.chat.id
        )

    if info_captcha is None:
        text = "Добро пожаловать! Пройдите проверку"
    else:
        text = html.escape(info_captcha["text_capcha"]) or "Добро пожаловать! Пройдите проверку"

    await callback.message.edit_text(f"Меню настройки капчи\n\nСтатус: <b>Включена</b>\n\nПриветствие: {text}",
                                     reply_markup=await keyboard_menu_setting_capcha(),
                                     parse_mode="HTML")
    await callback.answer()


WELCOME_NEW_USERS = "Добро пожаловать в группу, пройдите проверку на бота"


@command_router.callback_query(F.data == "setting_answer_capcha")
async def setting_answer_capcha(callback: CallbackQuery, pool: asyncpg.Pool, state: FSMContext):
    async with pool.acquire() as conn:
        await conn.execute(
            """
            insert into setting_capcha(text_capcha, chat_id)
            values ($1, $2) on conflict (chat_id)
            do
            update set text_capcha = excluded.text_capcha
            """,
            WELCOME_NEW_USERS, callback.message.chat.id
        )
    await state.set_state(Captcha.text)
    await callback.message.edit_text(text="Введите новое приветствие")
    await callback.answer()


@command_router.message(StateFilter(Captcha.text))
async def update_welcome_text_capcha(message: Message, bot: Bot, state: FSMContext, pool: asyncpg.Pool):
    await state.update_data(text_capcha=message.text)
    data = await state.get_data()

    async with pool.acquire() as conn:
        await conn.execute(
            """
            insert into setting_capcha(text_capcha, chat_id)
            values ($1, $2) on conflict (chat_id)
            do
            update set text_capcha = excluded.text_capcha
            """,
            data["text_capcha"], message.chat.id
        )

        info_captcha = await conn.fetchrow(
            """
            select status, text_capcha
            from setting_capcha
            where chat_id = $1
            """,
            message.chat.id
        )

    delete_message = await message.reply(text="Приветствие обновлено")
    await asyncio.sleep(1.3)
    await bot.delete_message(message_id=delete_message.message_id,
                             chat_id=message.chat.id)

    if info_captcha is None:
        status_flag = True
        text = "Добро пожаловать! Пройдите проверку"
    else:
        status_flag = info_captcha["status"]
        text = html.escape(info_captcha["text_capcha"]) or "Добро пожаловать! Пройдите проверку"

    status = "Включена" if status_flag else "Выключена"
    await message.answer(text=f"Меню настройки капчи\n\nСтатус: <b>{status}</b>\n\nПриветствие: {text}",
                         reply_markup=await keyboard_menu_setting_capcha(),
                         parse_mode="HTML")


@command_router.chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER))
async def capcha(event: ChatMemberUpdated, bot: Bot, state: FSMContext, pool: asyncpg.Pool):
    user = event.new_chat_member.user

    async with pool.acquire() as conn:
        await conn.execute(
            """
            insert into setting_capcha(chat_id)
            values ($1) on conflict (chat_id)
            do nothing
            """,
            event.chat.id
        )

        status_capcha = await conn.fetch(
            """
            select status
            from setting_capcha
            where chat_id = $1
            """,
            event.chat.id
        )

    if not status_capcha:
        return

    bot_member = await bot.get_chat_member(chat_id=event.chat.id, user_id=bot.id)
    if not bot_member.can_restrict_members:
        await bot.send_message(text="Бот не имеет прав для наложения ограничений",
                               chat_id=event.chat.id)
        return

    try:
        sent_message = await bot.send_message(
            chat_id=event.chat.id,
            text="Добро пожаловать в группу, пройдите тест",
            reply_markup=await button_for_capcha()
        )

        await state.set_state(Reg.captcha_message_id)

        await state.update_data(capcha_message_id=sent_message.message_id,
                                new_user_in_group_id=user.id)

        await bot.restrict_chat_member(
            chat_id=event.chat.id,
            user_id=user.id,
            permissions=ChatPermissions(can_send_messages=False,
                                        can_send_media_messages=False,
                                        can_send_polls=False,
                                        can_send_other_messages=False,
                                        can_add_web_page_previews=False,
                                        can_promote_users=False,
                                        can_pin_messages=False
                                        )
        )

        data = await state.get_data()

        asyncio.create_task(
            delete_capcha_unique_message_for_user(sent_message=data["capcha_message_id"], time_delete=2, bot=bot,
                                                  event=event, state=state))

    except Exception as e:
        await bot.ban_chat_member(event.chat.id, user.id)
        await event.answer(f"Не удалось отправить капчу. Пользователь {user.mention_html()} забанен.",
                           parse_mode="HTML")
        await bot.send_message(chat_id=1354347859,
                               text=f"Ошибка: {e}")


async def delete_capcha_unique_message_for_user(bot: Bot, sent_message, event: ChatMemberUpdated, time_delete: int,
                                                state: FSMContext):
    await asyncio.sleep(timedelta(minutes=time_delete).seconds)
    await bot.delete_message(message_id=sent_message,
                             chat_id=event.chat.id)
    await state.clear()


@command_router.callback_query(F.data == "button",
                               StateFilter(Reg.captcha_message_id))
async def capcha_command_keyboard_activated(callback: CallbackQuery, bot: Bot, state: FSMContext):
    data = await state.get_data()
    await bot.restrict_chat_member(
        chat_id=callback.message.chat.id,
        user_id=data["new_user_in_group_id"],
        permissions=ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_polls=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True
        )
    )

    await bot.delete_message(message_id=data["capcha_message_id"],
                             chat_id=callback.message.chat.id)


@command_router.message(F.chat.type != "private", Command("warn"))
async def warn_cmd(message: Message, bot: Bot, pool: asyncpg.Pool):
    if not message.reply_to_message:
        await message.reply("❗ Используйте эту команду в ответ на сообщение пользователя")
        return

    target_user = await bot.get_chat_member(chat_id=message.chat.id,
                                            user_id=message.reply_to_message.from_user.id)
    user = await bot.get_chat_member(chat_id=message.chat.id,
                                     user_id=message.from_user.id)
    bot_member = await bot.get_chat_member(chat_id=message.chat.id,
                                           user_id=bot.id)
    reply_member = message.reply_to_message.from_user

    check = AllCheck(user.status, target_user.status, bot_member, reply_member)
    await check.is_status(message)
    await check.is_member_bot(message)
    await check.is_can_ban(message)
    result = await check.result_check()

    if result == False:
        return

    if reply_member.is_bot:
        return await message.reply(text="Нельзя выдавать предупреждения боту")

    username = message.reply_to_message.from_user.username
    if username is None:
        username = message.from_user.first_name

    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO warn (user_id, warn_count, total_warn, chat_id, by_warn)
            VALUES ($1, 1, 1, $2, $3) ON CONFLICT (user_id) 
            DO
            UPDATE SET
                warn_count = warn.warn_count + 1,
                total_warn = warn.total_warn + 1
            """,
            reply_member.id, message.chat.id, username
        )

        warn_count = await conn.fetchval(
            "select warn_count from warn where user_id = $1 and chat_id = $2",
            reply_member.id, message.chat.id
        )

        is_banned = await conn.fetchval(
            "select ban from warn where user_id = $1 and chat_id = $2",
            reply_member.id, message.chat.id
        )

    chat = (await bot.get_chat(message.chat.id)).title
    if is_banned:
        try:
            await bot.ban_chat_member(user_id=reply_member.id, chat_id=message.chat.id)
            await bot.send_message(reply_member.from_user.id,
                                   f"{reply_member.mention_html()} был заблокирован за нарушения в группе <b>{chat}</b>",
                                   parse_mode="HTML")
            return
        except TelegramForbiddenError:
            await bot.send_message(message.chat.id,
                                   f"{reply_member.mention_html()} был заблокирован за нарушения в группе <b>{chat}</b>",
                                   parse_mode="HTML")
            return

    await message.answer(f"⚠️ Пользователь {reply_member.mention_html()} получил предупреждение.\n"
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


class CreatePoll(StatesGroup):
    chat_id = State()
    question = State()
    options = State()
    is_anonymous = State()
    type = State()
    allows_multiple_answers = State()
    poll_name = State()
    scheduled_time = State()


@command_router.message(F.chat.type == "private", Command("poll"))
async def cmd_poll(message: Message, state: FSMContext):
    await state.set_state(CreatePoll.chat_id)
    await message.reply(
        "Отправьте ссылку или ID группы\n\nЕсли хотите отменить создание опроса используйте команду <b>/cancel</b>",
        parse_mode="HTML")


@command_router.message(CreatePoll.chat_id)
async def cmd_reg_link_on_group(message: Message, bot: Bot, state: FSMContext):
    ## search_links_in_message = re.search(URL_PATTERN, message.text)
    # search_links_in_message = URL_PATTERN.search(message.text)

    # if search_links_in_message is None:
    #     await message.reply("Отправьте ссылку на группу")
    #     return

    # invite_link_part = search_links_in_message.group(0)

    # invite_link = search_links_in_message.group(0)
    #
    # # if invite_link_part.startswith('+'):
    # #     invite_link = invite_link_part
    # # else:
    # #     invite_link = f"joinchat/{invite_link_part}"
    #
    # chat = await bot.get_chat(invite_link)

    chat = message.text.strip()

    await state.update_data(chat_id=chat)

    member = await bot.get_chat_member(chat_id=chat, user_id=message.bot.id)

    if not member.can_pin_messages:
        await message.reply("У бота нет прав для отправки опроса в группу")
        return

    await state.set_state(CreatePoll.question)
    await message.reply("Теперь введите вопрос для опроса")


@command_router.message(CreatePoll.question)
async def cmd_reg_question(message: Message, state: FSMContext):
    await state.update_data(question=message.text)
    await state.set_state(CreatePoll.options)
    await message.reply("Теперь введите варианты ответов")


@command_router.message(CreatePoll.options)
async def cmd_reg_options(message: Message, state: FSMContext):
    options = [opt.strip() for opt in message.text.split(",") if opt.strip()]
    if len(options) < 2:
        await message.reply("В опросе должно быть минимум 2 ответа")
        return
    elif len(options) > 12:
        await message.reply("В опросе должно быть не больше 12 ответов")
        return

    await state.update_data(options=options)
    await state.set_state(CreatePoll.poll_name)
    await message.reply("Введите название опроса\n\nЕго видете только вы")


@command_router.message(CreatePoll.poll_name)
async def cmd_reg_poll_name(message: Message, state: FSMContext):
    await state.update_data(poll_name=message.text)
    await state.set_state(CreatePoll.is_anonymous)
    await message.reply("Сделать опрос анонимным?")


@command_router.message(CreatePoll.is_anonymous)
async def cmd_reg_is_anonymous(message: Message, state: FSMContext):
    if message.text.lower() == "да":
        await state.update_data(is_anonymous=True)
    elif message.text.lower() == "нет":
        await state.update_data(is_anonymous=False)
    else:
        await message.reply("Ответ должен быть 'Да' или 'Нет'")
        return

    await state.set_state(CreatePoll.allows_multiple_answers)
    await message.reply("Разрешить несколько ответов на вопрос?")


@command_router.message(CreatePoll.allows_multiple_answers)
async def cmd_reg_allows_multiple_answers(message: Message, state: FSMContext):
    if message.text.lower() == "да":
        await state.update_data(allows_multiple_answers=True)
    elif message.text.lower() == "нет":
        await state.update_data(allows_multiple_answers=False)
    else:
        await message.reply("Ответ должен быть 'Да' или 'Нет'")
        return

    await state.set_state(CreatePoll.scheduled_time)
    await message.reply(
        "Хотите отправить опрос сейчас или позже?\n\nЕсли позже, введите дату в следующем формате:\n<pre>День   |    час    |    минута</pre>",
        reply_markup=await keyboards_for_scheduled(),
        parse_mode="HTML")


@command_router.message(CreatePoll.scheduled_time)
async def cmd_reg_scheduled_time(message: Message, state: FSMContext, bot: Bot):
    if message.text.lower() == "сейчас":
        scheduled_time = datetime.now()

    elif ":" in message.text.lower():
        try:
            days, hours, minutes = map(int, message.text.split(":"))
            now = datetime.now()
            scheduled_time = now.replace(day=days, hour=hours, minute=minutes, second=0, microsecond=0)
            if scheduled_time < now:
                scheduled_time += timedelta(days=1)
        except:
            await message.reply("Неверный формат времени")
            return
    else:
        await message.reply("Ответ должен быть 'Сейчас' или 'Дата в формате который был предоставлен'")
        return

    await state.update_data(scheduled_time=scheduled_time)
    data = await state.get_data()
    if scheduled_time > datetime.now():
        delay = (scheduled_time - datetime.now()).total_seconds()
        asyncio.create_task(scheduled_send_poll(state=state, data=data, delay=delay, message=message, bot=bot))
    else:
        await send_poll(message=message, bot=bot, state=state, data=data)


async def scheduled_send_poll(message: Message, bot: Bot, state: FSMContext, data, delay):
    await asyncio.sleep(delay)
    await send_poll(message=message, bot=bot, state=state, data=data)


async def send_poll(message: Message, bot: Bot, state: FSMContext, data):
    group = await bot.get_chat(data["chat_id"])

    await bot.send_poll(
        chat_id=data["chat_id"],
        question=data["question"],
        options=data["options"],
        is_anonymous=data.get("is_anonymous", False),
        type="regular",
        allows_multiple_answers=data.get("allows_multiple_answers", False),
    )

    await bot.send_message(
        text=f"<code>{message.from_user.username}</code>, опрос <b><em>{data.get('poll_name')}</em></b> был успешно отправлен в группу <b><code>{group.title}</code></b>.",
        chat_id=message.from_user.id,
        parse_mode="HTML")

    await state.clear()


@command_router.message(Command("cancel"), F.chat.type == "private")
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.reply(text="Создание опроса было отменено")


@command_router.message(Command("chatID"))
async def cmd_chat_id(message: Message):
    await message.reply(text=f"ID чата: <code>{message.chat.id}</code>",
                        parse_mode="HTML")


@command_router.message(F.chat.type != "private", Command("kick"))
async def cmd_kik_users(message: Message, bot: Bot):
    if not message.reply_to_message:
        await message.reply("❗ Используйте эту команду в ответ на сообщение пользователя")
        return

    target_user = await bot.get_chat_member(chat_id=message.chat.id,
                                            user_id=message.reply_to_message.from_user.id)
    user = await bot.get_chat_member(chat_id=message.chat.id,
                                     user_id=message.from_user.id)
    bot_member = await bot.get_chat_member(chat_id=message.chat.id,
                                           user_id=bot.id)
    reply_member = message.reply_to_message.from_user

    check = AllCheck(user.status, target_user.status, bot_member, reply_member)
    await check.is_status(message)
    await check.is_member_bot(message)
    await check.is_can_ban(message)
    result = await check.result_check()

    if result == False:
        return

    reason = " ".join(message.text.split(" ")[1:]) or "Без причины"

    if reply_member.is_bot:
        return await message.reply(text="Бота нельзя кикнуть")

    try:
        await bot.ban_chat_member(chat_id=message.chat.id,
                                  user_id=reply_member.id,
                                  until_date=timedelta(seconds=30))

        user_name = reply_member.username or reply_member.first_name
        safe_reason = html.escape(reason)

        await message.answer(f"Пользователь @{user_name} был кикнут из группы\nПричина:\n<b>{safe_reason}</b>",
                             parse_mode="HTML")

    except Exception as e:
        await message.reply(f"Неизвестная ошибка: {e}")
        logging.error(f"Ошибка при исключении пользователя: {e}")


@command_router.message(F.text.startswith("/report"), F.chat.type == "private")
async def cmd_report(message: Message, bot: Bot):
    error_info = message.text
    try:
        if len(error_info) < 2:
            await bot.send_message(chat_id=message.from_user.id,
                                   text="Используйте: /report <информация про ошибки>")
            return

        await bot.send_message(chat_id=1354347859,
                               text=error_info.lower())

    except Exception as e:
        await bot.send_message(chat_id=message.from_user.id,
                               text=f"Ошибка: {e}")


@command_router.message(F.chat.type == "private", Command("support"))
async def cmd_support(message: Message, state: FSMContext):
    await state.set_state(Support.text_support)
    await message.reply("Опишите вашу проблему")


@command_router.message(StateFilter(Support.text_support))
async def cmd_support_text(message: Message, bot: Bot, state: FSMContext):
    try:
        await state.update_data(text_support=message.text.lower())
        data = await state.get_data()
        await bot.send_message(chat_id=1354347859,
                               text=data["text_support"])
    except Exception as e:
        await bot.send_message(chat_id=1354347859,
                               text=f"Ошибка: {e}")


@command_router.message(Command("total_warn"))
async def cmd_total_warn(message: Message, pool: asyncpg.Pool):
    async with pool.acquire() as conn:
        result = await conn.fetch(
            """
            select by_warn, total_warn from warn 
            order by total_warn desc LIMIT 3;
            """
        )

    if len(result) < 3:
        result.append({"by_warn": "unknown", "total_warn": 0})

    first_user = result[0]
    second_user = result[1]
    third_user = result[2]


    await message.reply(
        text=f"🥇1 место: {first_user["by_warn"]} - {first_user["total_warn"]}\n🥈2 место: {second_user["by_warn"]} - {second_user["total_warn"]}\n🥉3 место: {third_user["by_warn"]} - {second_user["total_warn"]}",
        parse_mode="HTML")


@command_router.message(Command("unwarn"))
async def cmd_unwarn(message: Message, pool: asyncpg.Pool):
    pass

