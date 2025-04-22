from aiogram import Router, types, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from keyboards.inline_keyboards import get_mode_keyboard, get_models_keyboard, get_providers_keyboard
from keyboards.reply_keyboards import get_settings_reply_keyboard
from registry import AIRegistry
from states import SettingsState, ChatState

router = Router()


@router.message(CommandStart())
async def command_start_handler(message: types.Message, state: FSMContext) -> None:
    await message.answer(
        "Привет! Добро пожаловать в бот.\n\n"
        "Пожалуйста, выберите режим работы бота:",
        reply_markup=get_mode_keyboard(),
    )
    await state.set_state(SettingsState.choosing_mode)


@router.callback_query(SettingsState.choosing_mode, F.data.startswith("mode_"))
async def choose_mode_handler(callback: types.CallbackQuery, state: FSMContext) -> None:
    mode = callback.data.split("_")[1]
    await state.update_data(mode=mode)

    if mode == "single":
        await callback.message.edit_text(
            "Вы выбрали обычный режим. Выберите провайдера:",
            reply_markup=get_providers_keyboard()
        )
        await state.set_state(SettingsState.choosing_provider)
    elif mode == "arena":
        await callback.message.edit_text(
            "Арена режим в разработке. Используйте обычный режим.",
            reply_markup=get_mode_keyboard()
        )
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
    await state.set_state(ChatState.waiting_query)
    await callback.answer()


@router.callback_query(SettingsState.choosing_model, F.data == "back_to_providers")
async def back_to_providers_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Выберите провайдера:",
        reply_markup=get_providers_keyboard()
    )
    await state.set_state(SettingsState.choosing_provider)
    await callback.answer()


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
    await state.set_state(ChatState.waiting_query)
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
    await message.answer(
        "Вы перешли в настройки. Выберите режим работы бота:",
        reply_markup=get_mode_keyboard()
    )
    await state.set_state(SettingsState.choosing_mode)
