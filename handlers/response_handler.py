import io
import aiogram.exceptions

from io import BytesIO
from PIL import Image
from aiogram import types
from utils.utils import split_text
from aiogram.enums import ParseMode
from aiogram.types import BufferedInputFile
from keyboards.reply_keyboards import get_settings_reply_keyboard


async def handle_model_response(message: types.Message, response):
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
