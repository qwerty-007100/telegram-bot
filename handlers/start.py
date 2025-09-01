from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from loader import answer_with_sticker
from keyboards import get_menu_for
from config import STICKER_WELCOME, ADMIN_ID, DOCTOR_ID
from keyboards.inline.admin_menu import admin_menu_kb
from database import create_user, get_user_by_tg

router = Router()


@router.message(F.text.startswith("/start"))
async def start_handler(message, state: FSMContext):
    args = message.text.split()
    referred_by = None

    if len(args) > 1 and args[1].isdigit():
        ref_id = int(args[1])
        if ref_id != message.from_user.id:
            referred_by = ref_id

    try:
        await state.clear()
    except Exception:
        pass

    user = create_user(
        tg_id=message.from_user.id,
        full_name=message.from_user.full_name,
        referred_by=referred_by
    )

    # Inform users that questions are currently unlimited/free
    free_info = "\n📌 Siz botdan bepul va cheksiz foydalanishingiz mumkin."

    bonus_text = ""
    if referred_by:
        bonus_text = "\n💰 Sizni referal orqali kirgan foydalanuvchi uchun 1000 so‘m bonus olindi!"

    # If admin/doctor started the bot, show admin menu instead of regular welcome
    if message.from_user.id in (ADMIN_ID, DOCTOR_ID):
        await answer_with_sticker(
            message,
            "Assalomu alaykum, admin! 👋\n\nBot admin paneliga xush kelibsiz.",
            sticker_file_id=STICKER_WELCOME,
            reply_markup=admin_menu_kb()
        )
        return

    await answer_with_sticker(
        message,
        f"Assalomu alaykum, {message.from_user.full_name}! 👋\n\n"
        "Siz botdan foydalanishni boshlashingiz mumkin." + free_info + bonus_text,
        sticker_file_id=STICKER_WELCOME,
        reply_markup=get_menu_for(message.from_user.id)
    )


@router.message(F.text == "/help")
async def help_handler(message, state: FSMContext):
    try:
        await state.clear()
    except Exception:
        pass
    text = (
        "🆘 Yordam:\n\n"
        "- '📑 Savol yozish' — shifokorga savol yuborish.\n"
        "- '📞 Admin bilan bog‘lanish' — admin kontaktlari.\n"
    )
    await answer_with_sticker(message, text, reply_markup=get_menu_for(message.from_user.id), sticker_file_id=STICKER_WELCOME)
