import io
import os
import tempfile

from PIL import Image
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from io import BytesIO
from ai import gemini, flux, whisper
from states import ChatState
from keyboards.reply_keyboards import get_settings_reply_keyboard
from aiogram.types import BufferedInputFile

router = Router()


async def нейросеть_1_заглушка(query: str) -> str:
    return f"Ответ от Нейросети 1 на запрос: '{query}' (это заглушка)"


async def нейросеть_2_заглушка(query: str) -> str:
    return f"Ответ от Нейросети 2 на запрос: '{query}' (это заглушка)"


@router.message(ChatState.waiting_query, F.voice)
async def voice_query_handler(message: types.Message, state: FSMContext) -> None:
    await message.answer("⏳")
    user_data = await state.get_data()
    network = user_data.get("network") or "default"

    voice = message.voice

    voice_bytes = await message.bot.download(voice)
    voice_data = BytesIO(voice_bytes.read())

    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as temp_audio:
        temp_audio.write(voice_data.read())
        audio_path = temp_audio.name

    try:
        transcription = whisper.transcribe_audio(audio_path)

        if "Error during transcription" in transcription:
            await message.answer(transcription, reply_markup=get_settings_reply_keyboard(), parse_mode="Markdown")
            return

        if network == "gemini":
            response = gemini.text_to_img_request(transcription)
        elif network == "1":
            response = await нейросеть_1_заглушка(transcription)
        elif network == "2":
            response = await нейросеть_2_заглушка(transcription)
        elif network == "flux":
            try:
                image: Image.Image = flux.generate_schnell(transcription)
                bio = io.BytesIO()
                image.save(bio, 'PNG')
                bio.seek(0)
                photo = BufferedInputFile(bio.read(), filename="image.png")
                await message.answer_photo(photo, reply_markup=get_settings_reply_keyboard())
                return
            except Exception as e:
                response = f"Произошла ошибка при генерации изображения: {e}"
        else:
            response = f"Вы в **обычном режиме**. Ответ от **дефолтной нейросети** (заглушка) на запрос: '{transcription}'"

        if response is None:
            response = "Произошла непредвиденная ошибка. Ответ от нейросети не получен."

        await message.answer(response, reply_markup=get_settings_reply_keyboard(), parse_mode="Markdown")

    finally:
        os.remove(audio_path)


@router.message(ChatState.waiting_query, F.photo)
async def photo_query_handler(message: types.Message, state: FSMContext) -> None:
    await message.answer("⏳")
    user_data = await state.get_data()
    network = user_data.get("network") or "default"
    photo = message.photo[-1]
    photo_bytes = await message.bot.download(photo)
    prompt = message.caption or ""

    if network == "gemini":
        image_bytes = BytesIO(photo_bytes.read())
        response = gemini.process_image_and_text(image_bytes, prompt)
    else:
        response = f"Вы в **обычном режиме**.  Обработка изображений доступна только для **Gemini**"

    await message.answer(response, reply_markup=get_settings_reply_keyboard(), parse_mode="Markdown")


@router.message(ChatState.waiting_query, F.text)
async def text_query_handler(message: types.Message, state: FSMContext) -> None:
    await message.answer("⏳")
    user_data = await state.get_data()
    network = user_data.get("network") or "default"
    query = message.text

    if network == "gemini":
        response = gemini.text_to_img_request(query)
    elif network == "1":
        response = await нейросеть_1_заглушка(query)
    elif network == "2":
        response = await нейросеть_2_заглушка(query)
    elif network == "flux":
        try:
            image: Image.Image = flux.generate_schnell(query)
            bio = io.BytesIO()
            image.save(bio, 'PNG')
            bio.seek(0)
            photo = BufferedInputFile(bio.read(), filename="image.png")
            await message.answer_photo(photo, reply_markup=get_settings_reply_keyboard())
            return
        except Exception as e:
            await message.answer(f"Произошла ошибка при генерации изображения: {e}")
            return
    else:
        response = f"Вы в **обычном режиме**. Ответ от **дефолтной нейросети** (заглушка) на запрос: '{query}'"

    await message.answer(response, reply_markup=get_settings_reply_keyboard(), parse_mode="Markdown")


@router.message(ChatState.waiting_query, F.content_types.ANY)
async def unknown_message_in_chat_handler(message: types.Message) -> None:
    await message.answer("Пожалуйста, отправьте текст, изображение или голосовое сообщение для обработки.")
