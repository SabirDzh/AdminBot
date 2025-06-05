from aiogram.utils.keyboard import (InlineKeyboardBuilder, ReplyKeyboardBuilder, KeyboardBuilder)
from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton,
                           InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove)
from app.database.requests import get_categories, get_category_item


async def inline_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="Создать пост", callback_data="CreatePost")
    builder.button(text="Редактировать пост", callback_data="EditPost")
    builder.button(text="Запланировать отправку", callback_data="schedule sending")
    builder.button(text="Удалить пост", callback_data="DeletePost")
    return builder.adjust(2).as_markup()


async def button_for_capcha():
    builder = InlineKeyboardBuilder()
    builder.button(text="Нажмите на кнопку", callback_data="button")
    return builder.adjust(1).as_markup()

