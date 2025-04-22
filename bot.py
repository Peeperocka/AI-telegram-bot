import handlers.settings_handlers as settings
import handlers.chat_handlers as chat
import asyncio
import os

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher


async def main():
    load_dotenv()
    # Импорт всех моделей и де-факто инициализация регистра.
    from ai import gemini, flux, llama, whisper, midjourney
    from registry import AIRegistry

    bot_apikey = os.environ["TELEGRAM_BOT_APIKEY"]
    bot = Bot(token=bot_apikey)
    dp = Dispatcher()

    dp.include_routers(settings.router, chat.router)

    await bot.delete_webhook()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
