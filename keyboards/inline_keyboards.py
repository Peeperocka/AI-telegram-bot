from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from registry import AIRegistry


def get_mode_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Обычный режим", callback_data="mode_single"),
            InlineKeyboardButton(text="Арена (в разработке)", callback_data="mode_arena")
        ]
    ])


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
