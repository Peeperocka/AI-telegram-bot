import asyncio
import os

from dotenv import load_dotenv

import handlers.settings_handlers as settings
import handlers.chat_handlers as chat

from aiogram import Bot, Dispatcher


async def main():
    load_dotenv()
    bot_apikey = os.environ["TELEGRAM_BOT_APIKEY"]
    bot = Bot(token=bot_apikey)
    dp = Dispatcher()

    dp.include_routers(settings.router, chat.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
