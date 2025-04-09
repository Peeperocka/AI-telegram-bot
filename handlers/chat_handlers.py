from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile

from ai import gemini
from states import ChatState, SettingsState
from keyboards.reply_keyboards import get_settings_reply_keyboard
from io import BytesIO

router = Router()


async def нейросеть_1_заглушка(query: str) -> str:
    return f"Ответ от Нейросети 1 на запрос: '{query}' (это заглушка)"


async def нейросеть_2_заглушка(query: str) -> str:
    return f"Ответ от Нейросети 2 на запрос: '{query}' (это заглушка)"


@router.message(ChatState.waiting_text_query, F.text)
async def text_query_handler(message: types.Message, state: FSMContext) -> None:
    user_data = await state.get_data()
    network = user_data.get("network") or "default"

    query = message.text

    if network == "3":
        image_data = gemini.text_to_img_request(query)
        if image_data:
            photo = BufferedInputFile(image_data.getvalue(), filename="image.png")
            await message.answer_photo(photo=photo, caption="Сгенерировано Gemini")
            return
        else:
            response = gemini.text_to_text_request(query)
    else:
        response = f"Вы в **обычном режиме**. Ответ от **дефолтной нейросети** (заглушка) на запрос: '{query}'"

    await message.answer(response, reply_markup=get_settings_reply_keyboard(), parse_mode="Markdown")


@router.message(ChatState.waiting_voice_query, F.voice)
async def voice_query_handler(message: types.Message, state: FSMContext) -> None:
    user_data = await state.get_data()
    network = user_data.get("network") or "default"

    voice = message.voice

    # TODO: реализовать перевод голоса в текст перед отправкой текста в ИИ
    voice_query = "голосовой запрос"

    if network == "1":
        response = await нейросеть_1_заглушка(voice_query)
    elif network == "2":
        response = await нейросеть_2_заглушка(voice_query)
    elif network == "3":
        image_data = gemini.text_to_img_request(voice_query)
        if image_data:
            photo = BufferedInputFile(image_data.getvalue(), filename="image.png")
            await message.answer_photo(photo=photo, caption="Сгенерировано Gemini")
            return
        else:
            response = gemini.text_to_text_request(voice_query)
    else:
        response = f"Вы в **обычном режиме**. Ответ на **голосовой запрос** от **дефолтной нейросети** (заглушка)"

    await message.answer(response, reply_markup=get_settings_reply_keyboard(), parse_mode="Markdown")


@router.message(ChatState.waiting_text_query, F.content_types.ANY)
@router.message(ChatState.waiting_voice_query, F.content_types.ANY)
async def unknown_message_in_chat_handler(message: types.Message) -> None:
    await message.answer("Пожалуйста, отправьте текст или голосовое сообщение для обработки.")
