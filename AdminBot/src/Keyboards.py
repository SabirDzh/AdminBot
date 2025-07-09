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


def edit_rule_group():
    builder = InlineKeyboardBuilder()
    builder.button(text="Изменить правила", callback_data="edit_rule_group")
    return builder.adjust(1).as_markup()


async def keyboards_for_poll():
    builder = ReplyKeyboardBuilder()
    builder.button(text="Да")
    builder.button(text="Нет")
    return builder.adjust(1).as_markup(resize_keyboard=True,
                                       one_time_keyboard=True,
                                       is_persistent=False)


async def keyboards_for_scheduled():
    builder = ReplyKeyboardBuilder()
    builder.button(text="Сейчас")
    builder.button(text="Позже")
    return builder.adjust(1).as_markup(resize_keyboard=True,
                                       one_time_keyboard=True,
                                       is_persistent=False)


async def keyboard_menu_setting_capcha():
    builder = InlineKeyboardBuilder()
    builder.button(text="Отключить капчу", callback_data="on_captcha")
    builder.button(text="Настроить приветствие капчи", callback_data="setting_answer_capcha")
    return builder.adjust(1).as_markup()


async def keyboard_menu_setting_capcha_two():
    builder = InlineKeyboardBuilder()
    builder.button(text="Включить капчу", callback_data="off_captcha")
    builder.button(text="Настроить приветствие капчи", callback_data="setting_answer_capcha")
    return builder.adjust(1).as_markup()
