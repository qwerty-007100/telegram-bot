from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
import asyncio

# Initialize Bot and Dispatcher with MemoryStorage so FSM works
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

async def set_bot_commands():
    """Set a minimal set of bot commands (best-effort)."""
    commands = [
        BotCommand(command="start", description="Botni ishga tushirish"),
        BotCommand(command="help", description="Yordam"),
    ]
    try:
        await bot.set_my_commands(commands)
    except Exception:
        # ignore errors setting commands
        pass

async def answer_with_sticker(message, text: str, sticker_file_id: str = None, reply_markup=None, parse_mode="Markdown"):
    """
    Send sticker (if provided and valid) then send the text reply.
    Sticker failures are ignored to avoid breaking UX.
    """
    if sticker_file_id:
        try:
            await message.answer_sticker(sticker=sticker_file_id)
        except Exception:
            # skip sticker errors
            pass
    # Send text (default parse_mode is Markdown)
    try:
        await message.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)
    except Exception:
        # Fallback: try sending without parse_mode
        await message.answer(text, reply_markup=reply_markup)
