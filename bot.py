import handlers.settings_handlers as settings
import handlers.single_chat_handlers as single_chat
import handlers.arena_chat_handlers as arena_chat
import asyncio
import os

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher


async def main():
    load_dotenv()
    # Импорт всех моделей и инициализация регистра.
    from ai import gemini, flux, llama, whisper, midjourney
    from registry import AIRegistry

    bot_apikey = os.environ["TELEGRAM_BOT_APIKEY"]
    bot = Bot(token=bot_apikey)
    dp = Dispatcher()

    dp.include_routers(settings.router, single_chat.router, arena_chat.router)

    await bot.delete_webhook(drop_pending_updates=False)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
