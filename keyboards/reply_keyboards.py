from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_settings_reply_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="/settings")],
    ], resize_keyboard=True)
    return keyboard
