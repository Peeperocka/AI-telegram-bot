import io
import aiogram.exceptions

from io import BytesIO
from PIL import Image
from aiogram import types
from utils.utils import split_text
from aiogram.enums import ParseMode
from aiogram.types import BufferedInputFile
from keyboards.reply_keyboards import get_settings_reply_keyboard


async def handle_model_response(message: types.Message, response) -> bool:
    success = False

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
                success = True
        except Exception as e:
            print(f"Error processing image response: {e}")
            try:
                await message.answer(
                    f"❌ Ошибка обработки изображения, пожалуйста, попробуйте позже.",
                    reply_markup=get_settings_reply_keyboard()
                )
            except Exception as send_error:
                print(f"Error sending image processing error message: {send_error}")
            success = False

    elif isinstance(response, str):
        if not response:
            try:
                await message.answer(
                    "Получен пустой ответ от модели.",
                    reply_markup=get_settings_reply_keyboard()
                )
            except Exception as send_error:
                print(f"Error sending empty response message: {send_error}")
            success = False
        else:
            message_parts = split_text(response)
            success = True
            for i, part in enumerate(message_parts):
                reply_markup = get_settings_reply_keyboard() if i == 0 else None
                try:
                    await message.answer(
                        text=part,
                        reply_markup=reply_markup,
                        parse_mode=ParseMode.MARKDOWN,
                        disable_web_page_preview=True
                    )
                except aiogram.exceptions.TelegramAPIError as e_md:
                    print(f"Markdown send failed: {e_md}. Retrying without Markdown.")
                    try:
                        await message.answer(
                            text=part,
                            reply_markup=reply_markup,
                            disable_web_page_preview=True
                        )
                    except aiogram.exceptions.TelegramAPIError as e_plain:
                        print(f"Plain text send also failed: {e_plain}")
                        error_msg = f"⚠️ Ошибка отправки части сообщения."
                        try:

                            if i == 0:
                                await message.answer(error_msg, reply_markup=get_settings_reply_keyboard())
                            else:
                                await message.answer(error_msg)
                        except Exception as final_send_error:
                            print(f"Error sending final error message: {final_send_error}")

                        success = False
                        break

    elif response is None:
        print("Received None response from model.")
        try:
            await message.answer(
                "🚫 Не удалось получить ответ от модели",
                reply_markup=get_settings_reply_keyboard()
            )
        except Exception as send_error:
            print(f"Error sending None response message: {send_error}")
        success = False

    else:
        print(f"Received unsupported response type: {type(response)}")
        print(f"Response content: {response}")
        try:
            await message.answer(
                "⚠️ Неподдерживаемый формат ответа от модели",
                reply_markup=get_settings_reply_keyboard()
            )
        except Exception as send_error:
            print(f"Error sending unsupported format message: {send_error}")
        success = False

    return success
