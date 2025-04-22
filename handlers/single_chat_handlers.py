import os
import tempfile

from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from io import BytesIO

from handlers.response_handler import handle_model_response
from states import ChatState
from keyboards.reply_keyboards import get_settings_reply_keyboard
from registry import AIRegistry, TextToTextModel, TextToImgModel, ImgToTextModel, AudioToTextModel

router = Router()


@router.message(ChatState.waiting_single_query, F.voice)
async def voice_query_handler(message: types.Message, state: FSMContext) -> None:
    await message.answer("⏳")
    user_data = await state.get_data()
    model_id = user_data.get("model_id", "default")
    registry = AIRegistry()

    try:
        voice = message.voice
        voice_bytes = await message.bot.download(voice)

        with tempfile.TemporaryDirectory() as temp_dir:
            audio_path = os.path.join(temp_dir, "audio.ogg")

            with open(audio_path, "wb") as f:
                f.write(voice_bytes.read())

            provider, version = model_id.split(":") if ":" in model_id else (None, None)
            model = registry.get_model(provider, version) if provider else None

            if model and AudioToTextModel in model.meta.capabilities:
                response = await model.execute(voice_bytes)
                return await handle_model_response(message, response)

            whisper_model = registry.get_model("whisper", "whisper-large-v3")
            if not whisper_model:
                await message.answer("⚠️ Ошибка транскрипции: модель не найдена")
                return

            transcription = await whisper_model.execute(audio_path)

            if not model:
                await message.answer(f"❓️ Модель {model_id} не найдена")
                return

            if TextToTextModel in model.meta.capabilities:
                response = await model.execute(transcription)
            elif TextToImgModel in model.meta.capabilities:
                response = await model.execute(transcription)
            else:
                response = f"🚫 Модель {model_id} не поддерживает голосовые запросы"

            await handle_model_response(message, response)

    except Exception as e:
        print(e)
        await message.answer(
            "🚫 Не удалось получить ответ от модели",
            reply_markup=get_settings_reply_keyboard(),
            parse_mode="Markdown"
        )


@router.message(ChatState.waiting_single_query, F.photo)
async def photo_query_handler(message: types.Message, state: FSMContext) -> None:
    await message.answer("⏳")
    user_data = await state.get_data()
    model_id = user_data.get("model_id", "default")
    registry = AIRegistry()

    try:
        photo = message.photo[-1]
        photo_bytes = await message.bot.download(photo)
        image_data = BytesIO(photo_bytes.read())
        prompt = message.caption or ""

        provider, version = model_id.split(":")
        model = registry.get_model(provider, version)

        if not model:
            await message.answer(f"❓️ Модель {model_id} не найдена")
            return

        if ImgToTextModel in model.meta.capabilities:
            response = await model.execute(image_data, prompt)
        else:
            response = f"🚫 Модель {model_id} не поддерживает обработку изображений"

        await handle_model_response(message, response)

    except Exception as e:
        print(e)
        await message.answer(f"⚠️ Ошибка, пожалуйста, попробуйте еще раз позже",
                             reply_markup=get_settings_reply_keyboard(), parse_mode="Markdown")


@router.message(ChatState.waiting_single_query, F.text)
async def text_query_handler(message: types.Message, state: FSMContext) -> None:
    await message.answer("⏳")
    user_data = await state.get_data()
    model_id = user_data.get("model_id", "default")
    registry = AIRegistry()

    try:
        if model_id == "default":
            await message.answer("Режим по умолчанию не активирован")
            return

        provider, version = model_id.split(":")
        model = registry.get_model(provider, version)

        if not model:
            await message.answer(f"Модель {model_id} не найдена")
            return

        if TextToTextModel in model.meta.capabilities or TextToImgModel in model.meta.capabilities:
            response = await model.execute(message.text)
            await handle_model_response(message, response)
        else:
            await message.answer(
                f"🚫 Модель {model_id} не поддерживает текстовые запросы",
                reply_markup=get_settings_reply_keyboard()
            )

    except ValueError as e:
        print(e)
        await message.answer("🚫 Не удалось получить ответ от модели", reply_markup=get_settings_reply_keyboard(),
                             parse_mode="Markdown")


@router.message(ChatState.waiting_single_query, F.content_types.ANY)
async def unknown_message_in_chat_handler(message: types.Message) -> None:
    await message.answer("Пожалуйста, отправьте текст, изображение или голосовое сообщение для обработки.")
