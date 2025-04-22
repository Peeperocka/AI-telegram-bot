from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from registry import AIRegistry
from states import MODE_SINGLE, MODE_ARENA


def get_mode_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="👤 Обычный режим", callback_data=f"mode_{MODE_SINGLE}"),
            InlineKeyboardButton(text="⚔️ Арена", callback_data=f"mode_{MODE_ARENA}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_arena_type_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="✍️ Текстовые ответы", callback_data="arena_type_text"),
        ],
        [
            InlineKeyboardButton(text="🖼️ Ответы изображениями", callback_data="arena_type_image"),
        ],
        [
            InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_mode")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_arena_vote_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="1️⃣ Ответ 1 лучше", callback_data="vote_1"),
            InlineKeyboardButton(text="2️⃣ Ответ 2 лучше", callback_data="vote_2"),
        ],
        [
            InlineKeyboardButton(text="👎 Ни один не нравится", callback_data="vote_none"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_providers_keyboard() -> InlineKeyboardMarkup:
    registry = AIRegistry()
    providers = registry.get_providers_to_user()

    buttons = []
    for provider in providers:
        buttons.append([
            InlineKeyboardButton(
                text=f"{provider.capitalize()} ➡️",
                callback_data=f"provider_{provider}"
            )
        ])

    buttons.append([InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_mode"
    )])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_models_keyboard(provider: str) -> InlineKeyboardMarkup:
    registry = AIRegistry()
    models = registry.get_models_for_provider(provider)

    buttons = []
    for model in models:
        version = model.meta.version
        btn_text = f"{version}"
        if model.meta.default:
            btn_text += " ★"

        buttons.append([
            InlineKeyboardButton(
                text=btn_text,
                callback_data=f"model_{provider}_{version}"
            )
        ])

    buttons.append([InlineKeyboardButton(
        text="◀️ Назад к провайдерам",
        callback_data="back_to_providers"
    )])

    return InlineKeyboardMarkup(inline_keyboard=buttons)
