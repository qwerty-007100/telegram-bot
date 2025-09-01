from aiogram import Router
from aiogram.types import Message
from keyboards import main_menu_keyboard
from loader import answer_with_sticker
from config import STICKER_WELCOME

router = Router()

@router.message(lambda m: m.text == "Bot haqida ma'lumot")
async def bot_info(message: Message):
    text = (
        "ℹ️ *Bot haqida ma'lumot*\n\n"
        "📅 Ishga tushirilgan sana: 01.09.2025\n"
        "🎯 Maqsad: Foydalanuvchilarga reproduktiv salomatlik bo'yicha yordam berish\n"
        "📖 To'liq tavsif: Ushbu bot orqali siz Doctor Mirsaid bilan bog'lanishingiz va boshqa ko'plab xizmatlardan foydalanishingiz mumkin.\n"
        "👨‍💻 Yaratuvchi: Botirov Bahodir (Telegram: @botirov207)\n"
        "📞 Telefon: +998 91 005 07 19\n"
        "🤝 Homiylar va hamkorlar: Mirsaid Bakumov va Bakumov Medical klinikasi\n\n"
    )
    await answer_with_sticker(
        message,
        text,
        sticker_file_id=STICKER_WELCOME,
        reply_markup=main_menu_keyboard,
        parse_mode="Markdown"
    )
