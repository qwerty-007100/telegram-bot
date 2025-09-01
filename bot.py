# bot.py
import asyncio
from aiogram import Bot, Dispatcher
from loader import dp, bot  # loader.py dan bot va dp ni olamiz
from handlers import register_all_handlers

async def main():
    # Barcha handlerlarni ro‘yxatdan o‘tkazamiz
    register_all_handlers(dp)

    # Bot pollingini ishga tushiramiz
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot to‘xtatildi.")
