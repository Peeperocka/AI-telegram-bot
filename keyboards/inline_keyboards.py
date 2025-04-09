from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_mode_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Обычный режим", callback_data="mode_single"),
            InlineKeyboardButton(text="Арена режим (placeholder)", callback_data="mode_arena"),
        ]
    ])
    return keyboard


def get_networks_single_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Нейросеть 1", callback_data="network_1")],
        [InlineKeyboardButton(text="Нейросеть 2", callback_data="network_2")],
        [InlineKeyboardButton(text="Gemini (Text & Image)", callback_data="network_3")],
        [InlineKeyboardButton(text="Назад к выбору режима", callback_data="back_to_mode")],
    ])
    return keyboard
