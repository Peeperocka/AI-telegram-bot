from aiogram import Router, types, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from keyboards.inline_keyboards import get_mode_keyboard, get_networks_single_keyboard
from keyboards.reply_keyboards import get_settings_reply_keyboard
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


@router.callback_query(SettingsState.choosing_mode, lambda c: c.data.startswith("mode_"))
async def choose_mode_handler(callback: types.CallbackQuery, state: FSMContext) -> None:
    mode = callback.data.split("_")[1]
    await state.update_data(mode=mode)

    if mode == "single":
        await callback.message.edit_text(
            "Вы выбрали **обычный режим**. Теперь выберите нейросеть:",
            reply_markup=get_networks_single_keyboard(),
            parse_mode="Markdown"
        )
        await state.set_state(SettingsState.choosing_network_single)
    elif mode == "arena":
        await callback.message.edit_text(
            "**Арена режим** пока находится в разработке.\n\n"
            "Вы будете получать ответы от нескольких нейросетей и выбирать лучший (функционал будет добавлен позже).\n\n"
            "Сейчас бот переключен в **обычный режим**.",
            parse_mode="Markdown"
        )
        await state.update_data(network="default")
        await state.set_state(ChatState.waiting_text_query)
    await callback.answer()


@router.callback_query(SettingsState.choosing_network_single, lambda c: c.data.startswith("network_"))
async def choose_network_single_handler(callback: types.CallbackQuery, state: FSMContext) -> None:
    network = callback.data.split("_")[1]
    await state.update_data(network=network)

    user_data = await state.get_data()
    mode = user_data.get("mode")
    network_name = user_data.get("network")
    await callback.message.delete()
    await callback.message.answer(
        f"Вы выбрали **обычный режим** и **Нейросеть {network_name}**.\n\n"
        "Теперь вы можете отправлять текстовые и голосовые запросы боту.\n\n"
        "Для вызова настроек используйте команду /settings или кнопку /settings в меню.",
        reply_markup=get_settings_reply_keyboard(),
        parse_mode="Markdown"
    )
    await state.set_state(ChatState.waiting_text_query)
    await callback.answer()


@router.callback_query(SettingsState.choosing_network_single, lambda c: c.data == "back_to_mode")
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
