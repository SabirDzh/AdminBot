TOKEN_API = "7352169865:AAHzuaDXNBkweoBs4bdBHO-LyjJ9ooTJxEQ"

#как правильнее писать @router.message or @dp.message
#почему используем bot.send_message
#как писать сокращенно, надо ли писать (Command(commands=""))


# from aiogram import Dispatcher, Bot, Router
# from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, ReplyParameters
# from aiogram.filters import Command
# import asyncio
# from config import TOKEN_API
#
# bot = Bot(TOKEN_API)
# dp = Dispatcher()
# router = Router()
# dp.include_router(router)
#
#
# kb = ReplyKeyboardMarkup(
#     keyboard=[
#         [KeyboardButton(text="/help")],
#         [KeyboardButton(text="/description"), KeyboardButton(text="/photo")]
#     ], resize_keyboard=True)
#
#
#
# HELP_COMMANDS = """
# <b>/start</b> - <em>запускает бота</em>
# <b>/help</b> - <em>все доступные команды</em>
# <b>/photo</b> - <em>отправляет изображение</em>
# <b>/description</b> - <em>информация о боте</em>
# """
#
# @router.message(Command(commands=["help"]))
# async def help_command(message: Message):
#     if not message.from_user.is_bot:
#         try:
#             await message.answer("Список команд был отправлен в лс!")
#             await bot.send_message(chat_id=message.from_user.id,
#                                    text=HELP_COMMANDS,
#                                    parse_mode="HTML")
#         except Exception as e:
#             await message.answer("Не получилось отправить в лс!")
#             await message.delete()
#     else:
#         await message.answer("Отправка сообщений ботам запрещена!")
#         await message.delete()
#
# @router.message(Command(commands=["start"]))
# async def start_command(message: Message):
#     # Создаём клавиатуру внутри функции
#
#     await bot.send_message(chat_id=message.from_user.id,
#                            text="Добро пожаловать в наш бот!",
#                            parse_mode="HTML",
#                            reply_markup=kb)
#
# @router.message(Command(commands=["description"]))
# async def description_command(message: Message):
#     await bot.send_message(chat_id=message.from_user.id,
#                            text="Наш бот умеет отправлять фотографии!",
#                            parse_mode="HTML")
#
# @router.message(Command(commands=["photo"]))
# async def photo_command(message: Message):
#     await bot.send_photo(chat_id=message.from_user.id,
#                          photo="")  # Укажите URL или file_id фото
#
# async def main():
#     print("Бот запущен!")
#     await dp.start_polling(bot, skip_updates=True)  # Исправлено skip_update на skip_updates
#
# if __name__ == "__main__":
#     asyncio.run(main())

"""РЕАЛИЗАЦИЯ ЗАМЕНЫ КНОПОК И УДАЛЕНИЕ ОБЪЕКТА СООБЩЕНИЯ БОТА"""
# new_ikb = InlineKeyboardBuilder()
# new_ikb.button(text="Удалить фотографию", callback_data="btn1")
# new_ikb.button(text="Поставить оценку фото", callback_data="btn2")
# new_ikb.adjust(2)
# first_keyboard = new_ikb.as_markup()
#
# new_second_ikb = InlineKeyboardBuilder()
# new_second_ikb.button(text="❤️", callback_data="like")
# new_second_ikb.button(text="👎", callback_data="dislike")
# new_second_ikb.button(text="Вернуться назад", callback_data="back")
# new_second_ikb.adjust(2)
# second_keyboard = new_second_ikb.as_markup()
#
# @router.message(Command(commands=["start"]))
# async def start_cmd(message: Message) -> None:
#     await bot.send_photo(chat_id=message.from_user.id,
#                          photo="https://fotolandscape.com/blog/linii-v-pejzazhe/",
#                          caption="Нравится ли тебе фотография?",
#                          reply_markup=first_keyboard)
#
#
# @dp.callback_query()
# async def ikb_cb_handler(callback: CallbackQuery) -> None:
#     if callback.data == "btn2":
#         await callback.message.edit_reply_markup(reply_markup=second_keyboard)
#     elif callback.data == "btn1":
#         await callback.message.delete()
#     elif callback.data == "back":
#         await callback.message.edit_reply_markup(reply_markup=first_keyboard)
#
#     global proverca
#     proverca = False
#
#     if proverca == False:
#         if callback.data == "like":
#             await callback.answer(show_alert=False,
#                                   text="Вы поставили лайк")
#             proverca = True
#         elif callback.data == "dislike":
#             await callback.answer(show_alert=False,
#                                   text="Вы поставили дизлайк")
#             proverca = True
#
#     elif proverca == True:
#         await callback.answer("Ты уже голосовал!", show_alert=True)
#
#     await callback.answer()



# bot = Bot(TOKEN_API)
# dp = Dispatcher()
# router = Router()
# dp.include_router(router)
#
# number = 0
#
# ikb = InlineKeyboardBuilder()
# ikb.button(text="Button", callback_data="btn1")
# ikb.adjust()
# keyboard = ikb.as_markup()
#
#
# def get_inline_keyboard() -> InlineKeyboardMarkup:
#     first_keyboard = InlineKeyboardBuilder()
#     first_keyboard.button(text="Increase", callback_data="btn_increase")
#     first_keyboard.button(text="Decrease", callback_data="btn_decrease")
#     first_keyboard.button(text="Random number", callback_data="btn_random_number")
#     first_keyboard.adjust(2)
#     return first_keyboard.as_markup()
#
#
# @router.message(Command("start"))
# async def start_cmd(message: Message) -> None:
#     user_name_id = message.from_user.first_name
#     await message.answer(text=f"Рады вас видеть, {user_name_id}",
#                          reply_markup=keyboard)
#
#
# @router.callback_query()
# async def ikb_kb_handler(callback: CallbackQuery) -> None:
#     await callback.answer("Something!", show_alert=True)
#
#
# @router.callback_query(lambda callback_query: callback_query.data.startswith("btn"))
# async def ikb_cb_handler(callback: CallbackQuery, state: FSMContext) -> None:
#     global number
#     if callback.data == "btn_increase":
#         number += 1
#         await callback.message.edit_text(f"The current number is {number}",
#                                          reply_markup=get_inline_keyboard())
#     elif callback.data == "btn_decrease":
#         number -= 1
#         await callback.message.edit_text(f"The current number is {number}",
#                                          reply_markup=get_inline_keyboard())
#     elif callback.data == "btn_random_number":
#         await callback.message.edit_text(text="Введите любое число:")
#         # await state.set_state(Form.number)
#         # number = int(message.text)
#         num = randint(0, 20)
#         await callback.message.edit_text(f"The current number is {num}",
#                                          reply_markup=get_inline_keyboard())
#         await state.clear()
#
#     await callback.answer()
#
#
# @router.inline_query()
# async def inline_echo(inline_query: InlineQuery) -> None:
#     text = inline_query.query or "Echo" # получаем текст от пользователя
#     input_content = InputTextMessageContent(message_text=text) # формируем ответ для пользователя
#     result_id = hashlib.md5(text.encode()).hexdigest() # создали уникальный ID результата
#
#     item = InlineQueryResultArticle(
#         input_message_content=input_content,
#         id=result_id,
#         title="Echo",
#         thumbnail_url="https://via.placeholder.com/100"  # необязательная иконка"
#     )
#
#     await bot.answer_inline_query(inline_query_id=inline_query.id,
#                                   results=[item],
#                                   cache_time=1)
#
#     # await inline_query.answer(
#     #     results=[item],
#     #     cache_time=1,
#     #     is_personal=True
#     # )
