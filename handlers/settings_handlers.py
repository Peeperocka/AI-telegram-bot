import asyncio
import database

from aiogram import Router, types, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove
from keyboards.inline_keyboards import get_mode_keyboard, get_models_keyboard, get_providers_keyboard, \
    get_arena_type_keyboard
from keyboards.reply_keyboards import get_settings_reply_keyboard
from registry import AIRegistry
from states import SettingsState, ChatState

router = Router()


@router.message(CommandStart())
async def command_start_handler(message: types.Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    user_name = message.from_user.full_name

    print(f"User {user_name} (ID: {user_id}) started the bot.")

    try:
        database.register_or_check_user(user_id)
        print(f"User {user_id} checked/registered in DB.")

    except Exception as e:
        print(f"Error registering/checking user {user_id} in DB: {e}")

    await message.answer(
        f"Привет, {user_name}! Добро пожаловать.\n\n"
        "Пожалуйста, выберите режим работы бота:",
        reply_markup=get_mode_keyboard(),
    )
    await state.set_state(SettingsState.choosing_mode)


@router.callback_query(SettingsState.choosing_mode, F.data.startswith("mode_"))
async def choose_mode_handler(callback: types.CallbackQuery, state: FSMContext) -> None:
    mode = callback.data.split("_")[1]
    await state.update_data(mode=mode)

    await callback.message.delete()

    if mode == "single":
        await callback.message.answer(
            "Выбран 'Обычный режим'.\n"
            "Выберите провайдера AI модели:",
            reply_markup=get_providers_keyboard()
        )
        await state.set_state(SettingsState.choosing_provider)
    elif mode == "arena":
        await callback.message.answer(
            "Выбран режим '✨ Арена ✨'.\n"
            "Выберите тип арены (какой результат вы хотите сравнивать):",
            reply_markup=get_arena_type_keyboard()
        )
        await state.set_state(SettingsState.choosing_arena_type)
    await callback.answer()


@router.callback_query(SettingsState.choosing_arena_type, F.data.startswith("arena_type_"))
async def choose_arena_type_handler(callback: types.CallbackQuery, state: FSMContext):
    arena_type_callback_data = callback.data

    arena_type_raw = arena_type_callback_data.split("_")[-1]

    if arena_type_raw not in ["text", "image"]:
        print(f"Получен некорректный arena_type колбэк: {callback.data}")
        await callback.answer("Неизвестный тип арены.", show_alert=True)
        return

    await state.update_data(arena_type=arena_type_raw)

    arena_type_name_display = {
        "text": "✍️ Текстовые ответы",
        "image": "🖼️ Ответы изображениями (Запросы на английском)"
    }.get(arena_type_raw, "Неизвестный тип")

    await callback.message.delete()
    await callback.message.answer(
        f"✨ Арена типа '{arena_type_name_display}' выбрана! ✨\n\n"
        "Теперь отправьте ваш **первый запрос** (текст или голос) для сравнения моделей.\n"
        "Модели будут выбраны автоматически.",
        reply_markup=get_settings_reply_keyboard()
    )

    await state.set_state(ChatState.waiting_arena_query)
    await callback.answer()


@router.callback_query(SettingsState.choosing_provider, F.data.startswith("provider_"))
async def choose_provider_handler(callback: types.CallbackQuery, state: FSMContext):
    provider = callback.data.split("_")[1]
    await state.update_data(current_provider=provider)

    await callback.message.edit_text(
        f"Выберите версию {provider}:",
        reply_markup=get_models_keyboard(provider)
    )
    await state.set_state(SettingsState.choosing_model)
    await callback.answer()


@router.callback_query(SettingsState.choosing_model, F.data.startswith("model_"))
async def choose_model_handler(callback: types.CallbackQuery, state: FSMContext):
    _, provider, version = callback.data.split("_")

    await state.update_data(
        model_id=f"{provider}:{version}",
        model_name=f"{provider} {version}"
    )

    await callback.message.delete()
    await callback.message.answer(
        f"✅ Выбрана модель: {version}\n"
        f"Это {AIRegistry().get_model(provider, version).meta.description}\n"
        "Теперь можете отправлять запросы!",
        reply_markup=get_settings_reply_keyboard()
    )
    await state.set_state(ChatState.waiting_single_query)
    await callback.answer()


@router.callback_query(SettingsState.choosing_model, F.data == "back_to_providers")
async def back_to_providers_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Выберите провайдера:",
        reply_markup=get_providers_keyboard()
    )
    await state.set_state(SettingsState.choosing_provider)
    await callback.answer()


@router.callback_query(SettingsState.choosing_arena_type, F.data == "back_to_mode")
@router.callback_query(SettingsState.choosing_provider, F.data == "back_to_mode")
async def back_to_mode_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Выберите режим работы бота:",
        reply_markup=get_mode_keyboard()
    )
    await state.set_state(SettingsState.choosing_mode)
    await callback.answer()


@router.callback_query(SettingsState.choosing_provider, F.data.startswith("model_"))
async def choose_model_handler(callback: types.CallbackQuery, state: FSMContext):
    _, provider, version = callback.data.split("_")
    await state.update_data(
        model_id=f"{provider}:{version}",
        model_name=f"{provider} {version}"
    )
    await callback.message.delete()
    await callback.message.answer(
        f"Выбрана модель: {provider} {version}",
        reply_markup=get_settings_reply_keyboard()
    )
    await state.set_state(ChatState.waiting_single_query)
    await callback.answer()


@router.callback_query(SettingsState.choosing_model, lambda c: c.data == "back_to_mode")
async def back_to_mode_handler(callback: types.CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_text(
        "Выберите режим работы бота:",
        reply_markup=get_mode_keyboard()
    )
    await state.set_state(SettingsState.choosing_mode)
    await callback.answer()


@router.message(Command(commands="settings"))
@router.message(F.text.lower() == "/settings")
async def settings_command_handler(message: types.Message, state: FSMContext) -> None:
    temp_msg = await message.answer("⚙️ Перехожу в настройки...", reply_markup=ReplyKeyboardRemove())
    await asyncio.sleep(0.5)
    await temp_msg.delete()
    await message.answer(
        "Вы перешли в настройки. Выберите режим работы бота:",
        reply_markup=get_mode_keyboard(),
    )
    await state.set_state(SettingsState.choosing_mode)
