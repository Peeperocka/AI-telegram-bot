import io
import os
import tempfile
import aiogram.exceptions

from PIL import Image
from aiogram import Router, types, F
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from io import BytesIO
from states import ChatState
from keyboards.reply_keyboards import get_settings_reply_keyboard
from aiogram.types import BufferedInputFile
from registry import AIRegistry, TextToTextModel, TextToImgModel, ImgToTextModel, AudioToTextModel
from utils.utils import split_text

router = Router()


async def _handle_model_response(message: types.Message, response):
    if isinstance(response, BytesIO):
        try:
            response.seek(0)
            with Image.open(response) as img:
                bio = io.BytesIO()
                img.save(bio, 'PNG')
                bio.seek(0)
                await message.answer_photo(
                    BufferedInputFile(bio.read(), filename="image.png"),
                    reply_markup=get_settings_reply_keyboard()
                )
        except Exception as e:
            print(e)
            await message.answer(
                f"❌ Ошибка обработки изображения, пожалуйста, попробуйте позже.",
                reply_markup=get_settings_reply_keyboard()
            )
    elif isinstance(response, str):
        message_parts = split_text(response)
        for i, part in enumerate(message_parts):
            reply_markup = get_settings_reply_keyboard() if i == 0 else None
            try:
                await message.answer(
                    text=part,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True
                )
            except aiogram.exceptions.TelegramAPIError as e:
                print(e)
                error_msg = f"⚠️ Ошибка отправки сообщения"
                try:
                    await message.answer(
                        text=part.replace("*", ""),
                        reply_markup=reply_markup
                    )
                except aiogram.exceptions.TelegramAPIError as e:
                    print(e)
                    if i == 0:
                        await message.answer(error_msg, reply_markup=get_settings_reply_keyboard())
                    else:
                        await message.answer(error_msg)
                    break

    elif response is None:
        await message.answer(
            "🚫 Не удалось получить ответ от модели",
            reply_markup=get_settings_reply_keyboard()
        )

    else:
        print(type(response))
        print(response)
        await message.answer(
            "⚠️ Неподдерживаемый формат ответа",
            reply_markup=get_settings_reply_keyboard()
        )


@router.message(ChatState.waiting_query, F.voice)
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
                return await _handle_model_response(message, response)

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

            await _handle_model_response(message, response)

    except Exception as e:
        print(e)
        await message.answer(
            "🚫 Не удалось получить ответ от модели",
            reply_markup=get_settings_reply_keyboard(),
            parse_mode="Markdown"
        )


@router.message(ChatState.waiting_query, F.photo)
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

        if model_id == "default":
            await message.answer("Режим по умолчанию не поддерживает изображения")
            return

        provider, version = model_id.split(":")
        model = registry.get_model(provider, version)

        if not model:
            await message.answer(f"❓️ Модель {model_id} не найдена")
            return

        if ImgToTextModel in model.meta.capabilities:
            response = await model.execute(image_data, prompt)
        else:
            response = f"🚫 Модель {model_id} не поддерживает обработку изображений"

        await _handle_model_response(message, response)

    except Exception as e:
        print(e)
        await message.answer(f"⚠️ Ошибка, пожалуйста, попробуйте еще раз позже",
                             reply_markup=get_settings_reply_keyboard(), parse_mode="Markdown")


@router.message(ChatState.waiting_query, F.text)
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
            await _handle_model_response(message, response)
        else:
            await message.answer(
                f"🚫 Модель {model_id} не поддерживает текстовые запросы",
                reply_markup=get_settings_reply_keyboard()
            )

    except ValueError as e:
        print(e)
        await message.answer("🚫 Не удалось получить ответ от модели", reply_markup=get_settings_reply_keyboard(),
                             parse_mode="Markdown")


@router.message(ChatState.waiting_query, F.content_types.ANY)
async def unknown_message_in_chat_handler(message: types.Message) -> None:
    await message.answer("Пожалуйста, отправьте текст, изображение или голосовое сообщение для обработки.")
