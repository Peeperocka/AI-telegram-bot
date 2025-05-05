from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from io import BytesIO

from database import can_afford_cost, get_user_quota_info, DEFAULT_DAILY_QUOTA, quota_check
from handlers.response_handler import handle_model_response
from states import ChatState
from keyboards.reply_keyboards import get_settings_reply_keyboard
from registry import AIRegistry, TextToTextModel, TextToImgModel, ImgToTextModel, AudioToTextModel
from utils.transcription import transcribe_voice_message

router = Router()


@router.message(ChatState.waiting_single_query, F.voice)
@quota_check(1)
async def voice_query_handler(message: types.Message, state: FSMContext) -> None:
    await message.answer("⏳")
    user_data = await state.get_data()
    model_id = user_data.get("model_id", "default")
    registry = AIRegistry()

    try:
        provider, version = model_id.split(":")
        model = registry.get_model(provider, version)

        if not model:
            await message.answer(f"❓️ Модель {model_id} не найдена")
            return

        response = None

        if AudioToTextModel in model.meta.capabilities:
            voice = message.voice
            voice_bytes = await message.bot.download(voice)
            voice_data = BytesIO(voice_bytes.read())
            response = await model.execute(voice_data)
        elif TextToTextModel in model.meta.capabilities or TextToImgModel in model.meta.capabilities:
            text = await transcribe_voice_message(message, registry)
            response = await model.execute(text)

        await handle_model_response(message, response)

    except Exception as e:
        print(e)
        await message.answer(
            "🚫 Не удалось получить ответ от модели",
            reply_markup=get_settings_reply_keyboard(),
            parse_mode="Markdown"
        )


@router.message(ChatState.waiting_single_query, F.photo)
@quota_check(1)
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
@quota_check(1)
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
