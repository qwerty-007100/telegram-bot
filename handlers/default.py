from aiogram import Router, types
from aiogram.filters import CommandStart
from loader import answer_with_sticker
from config import STICKER_WELCOME
from keyboards import main_menu_keyboard

router = Router()


@router.message(CommandStart())
async def cmd_start(message: types.Message):
    await answer_with_sticker(
        message,
        "Welcome! Bot bilan bog'lanish uchun pastdagi menyudan foydalaning.",
        sticker_file_id=STICKER_WELCOME,
        reply_markup=main_menu_keyboard
    )


# Note: removed broad fallback to avoid intercepting valid button presses.
# If you need a fallback, make it highly specific so it doesn't override real handlers.
