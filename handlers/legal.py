from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards.inline.legal import legal_accept_kb, legal_menu_kb
from loader import answer_with_sticker
from config import STICKER_WELCOME

router = Router()

class LegalForm(StatesGroup):
    awaiting_acceptance = State()

# Privacy Policy handler
@router.message(F.text == "Maxfiylik siyosati")
async def privacy_policy(message: Message):
    text = (
        "📜 *Maxfiylik siyosati*\n\n"
        "1. Foydalanuvchi ma’lumotlari uchinchi tomonlarga berilmaydi.\n"
        "2. Ro‘yxatdan o‘tish paytida kiritilgan barcha ma’lumotlar faqat xizmat ko‘rsatish maqsadida saqlanadi.\n"
        "3. Foydalanuvchi ma’lumotlari xavfsizligi ta’minlanadi va qonuniy muddat davomida saqlanadi.\n"
    )
    await answer_with_sticker(
        message,
        text,
        sticker_file_id=STICKER_WELCOME,
        parse_mode="Markdown"
    )

# Medical Disclaimer handler
@router.message(F.text == "Tibbiy maslahatlar ogohlantirishi")
async def medical_disclaimer(message: Message):
    text = (
        "⚠️ *Tibbiy maslahatlar ogohlantirishi*\n\n"
        "1. Bot orqali berilgan maslahatlar faqat maslahat xarakterida.\n"
        "2. Aniqlik va davolash faqat malakali shifokor ko‘rigidan so‘ng amalga oshiriladi.\n"
        "3. Bot orqali berilgan maslahatlar shaxsiy tibbiy konsultatsiya o‘rnini bormaydi.\n"
    )
    await answer_with_sticker(
        message,
        text,
        sticker_file_id=STICKER_WELCOME,
        parse_mode="Markdown"
    )

# Enforce acceptance during registration
@router.message(F.text == "Ro'yxatdan o'tish")
async def start_registration(message: Message, state: FSMContext):
    await state.set_state(LegalForm.awaiting_acceptance)
    text = (
        "📜 *Maxfiylik siyosati va Tibbiy maslahatlar ogohlantirishi*\n\n"
        "Iltimos, xizmatlardan foydalanishdan oldin quyidagi qoidalarni qabul qiling:\n"
        "1. Foydalanuvchi ma’lumotlari uchinchi tomonlarga berilmaydi.\n"
        "2. Bot orqali berilgan maslahatlar faqat maslahat xarakterida.\n"
        "3. Aniqlik va davolash faqat malakali shifokor ko‘rigidan so‘ng amalga oshiriladi.\n\n"
        "Agar qoidalarni qabul qilsangiz, pastdagi tugmani bosing."
    )
    await answer_with_sticker(
        message,
        text,
        sticker_file_id=STICKER_WELCOME,
        reply_markup=legal_accept_kb(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "accept_legal")
async def accept_legal(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    # Acknowledge callback to remove loading indicator
    try:
        await callback.answer()
    except Exception:
        pass

    await state.clear()
    await callback.message.edit_text(
        "✅ Siz qoidalarni qabul qildingiz. Endi ro‘yxatdan o‘tishingiz mumkin.",
        reply_markup=None
    )
    # Redirect to registration flow
    from handlers.register import start_register
    await start_register(callback.message, state)
