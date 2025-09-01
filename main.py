import asyncio
from aiogram.exceptions import TelegramConflictError
from loader import dp, bot, set_bot_commands, storage
from register_all_handlers import register_all_handlers
from scheduler import start_scheduler


async def main():
    # Register routers
    register_all_handlers(dp)

    # Set bot commands (best-effort)
    await set_bot_commands()

    # Ensure no webhook is set (delete if present) to avoid TelegramConflictError
    try:
        await bot.delete_webhook(drop_pending_updates=True)
    except Exception:
        # ignore failures here; we'll handle conflict below
        pass

    # Start background scheduler
    try:
        asyncio.create_task(start_scheduler(bot))
    except Exception:
        pass

    print("Bot ishga tushdi...")

    # Start long-polling with a small retry if Telegram reports a conflict
    try:
        await dp.start_polling(bot)
    except TelegramConflictError as e:
        print("TelegramConflictError: attempting to delete webhook and retry...")
        try:
            await bot.delete_webhook(drop_pending_updates=True)
        except Exception:
            pass
        # one retry
        await dp.start_polling(bot)
    finally:
        # Graceful shutdown: close storage and bot session
        try:
            await storage.close()
        except Exception:
            pass
        try:
            await bot.session.close()
        except Exception:
            pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Interrupted by user, exiting...")
