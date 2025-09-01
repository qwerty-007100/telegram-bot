import asyncio
import logging
import importlib

from aiogram.types import BotCommand
from loader import dp, bot

# Import the handlers.register_all_handlers module explicitly to avoid name shadowing
register = importlib.import_module('handlers.register_all_handlers')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def set_bot_commands() -> None:
    commands = [
        BotCommand(command="start", description="Botni ishga tushirish"),
        BotCommand(command="help", description="Yordam"),
        BotCommand(command="tarif", description="Tariflar va sotib olish"),
    ]
    try:
        await bot.set_my_commands(commands)
        logger.info("Bot commands set")
    except Exception as exc:
        logger.warning("Failed to set bot commands: %s", exc)

async def main() -> None:
    # Register all handlers (routers) before starting polling
    try:
        register.register_all_handlers(dp)
    except Exception as exc:
        logger.exception("Failed to register handlers: %s", exc)
        # proceed — registraton failures will be logged

    # Set bot commands (best-effort)
    await set_bot_commands()

    logger.info("Starting polling...")
    try:
        await dp.start_polling(bot)
    finally:
        # Ensure bot session closed on shutdown
        try:
            await bot.session.close()
        except Exception:
            pass

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped by user")
