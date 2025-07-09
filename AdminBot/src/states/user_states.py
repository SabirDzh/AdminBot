from aiogram.fsm.state import *


class Captcha(StatesGroup):
    text = State()


class Support(StatesGroup):
    text_support = State()
