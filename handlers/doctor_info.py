from aiogram import Router
from aiogram.types import Message
from keyboards import main_menu_keyboard
from loader import answer_with_sticker
from config import STICKER_WELCOME

router = Router()

# Doctor haqida ma'lumot
@router.message(lambda m: m.text == "Doctor Mirsaid haqida")
async def doctor_info(message: Message):
    text = (
        "👨‍⚕ **Doctor MIRSAID haqida**\n\n"
        "📅 Tug‘ilgan yili: 1997\n"
        "🎓 Oliy ta’lim: Toshkent Tibbiyot Akademiyasi\n"
        "🏥 Yo‘nalish: Reproduktologiya\n"
        "🧑‍⚕ Ish tajribasi: 5 yildan ortiq\n"
        "👶 Yordam bergan oilalar soni: 350 dan ortiq\n"
        "⏰ Ish vaqti: 08:00 — 20:00\n"
        "📍 Ish joyi: Bakumov Medical klinikasi\n\n"
        "Siz ham professional yordam olishingiz mumkin!"
    )
    await answer_with_sticker(
        message,
        text,
        sticker_file_id=STICKER_WELCOME,
        reply_markup=main_menu_keyboard,
        parse_mode="Markdown"
    )
