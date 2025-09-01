# handlers/ask_question.py
from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from config import ADMIN_ID, DOCTOR_ID, STICKER_TARIFF
from keyboards import get_menu_for
from loader import bot, answer_with_sticker
from database import get_user_by_tg, Session

router = Router()


class QuestionFSM(StatesGroup):
    waiting_for_text = State()


# --- Savol yozish tugmasi: sets FSM state ---
@router.message(lambda m: m.text in ["📑 Savol yozish", "Savol yozish"])
async def start_ask_question(message: Message, state: FSMContext):
    user = get_user_by_tg(message.from_user.id)
    if not user:
        await answer_with_sticker(
            message,
            "❗ Savol yozish uchun avval ro'yxatdan o'tishingiz kerak.",
            sticker_file_id=STICKER_TARIFF
        )
        return

    await state.set_state(QuestionFSM.waiting_for_text)
    await message.answer("✍️ Iltimos, savolingizni yozib yuboring.")


# --- Process question only when FSM state is active ---
@router.message(QuestionFSM.waiting_for_text)
async def process_question(message: Message, state: FSMContext):
    session = Session()
    user = get_user_by_tg(message.from_user.id)

    if not user:
        await answer_with_sticker(
            message,
            "❗ Savol yozish uchun avval ro'yxatdan o'tishingiz kerak.",
            sticker_file_id=STICKER_TARIFF
        )
        await state.clear()
        session.close()
        return

    # Userni DB session orqali olish
    user_db = session.query(type(user)).filter_by(id=user.id).first()

    # Quotas and tariffs disabled: allow unlimited questions for users.
    # Keep DB session for compatibility but do not decrement any counters.
    try:
        session.commit()
    except Exception:
        try:
            session.rollback()
        except Exception:
            pass

    question_text = message.text.strip()
    info = (
        f"📩 Yangi savol!\n\n"
        f"👤 Ismi: {user.full_name}\n"
        f"📞 Telefon raqami: {user.phone or '—'}\n"
        f"📌 Tarif: {user_db.tariff or 'Bepul (2 ta savol)'}\n"
        f"🔢 Qolgan kunlik savollar: {user_db.daily_remaining}\n\n"
        f"❓ Savol: {question_text}"
    )

    # Admin va doktorga yuborish (buzilmaslik uchun xatolarni ushlaymiz)
    try:
        from aiogram.utils.exceptions import TelegramBadRequest
    except Exception:
        # aiogram v3+ exposes exceptions in aiogram.exceptions
        from aiogram.exceptions import TelegramBadRequest
    # Persist question so replies can reference which question was answered
    try:
        from database import create_question
        qid = create_question(user.telegram_id, question_text)
    except Exception:
        qid = None

    # Build an inline keyboard so staff can reply to this specific question
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    # Include question id in callback_data: reply_q_<tg>_<qid>
    cb_data = f"reply_q_{user.telegram_id}"
    if qid:
        cb_data = f"reply_q_{user.telegram_id}_{qid}"
    ikb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Javob berish", callback_data=cb_data)]
    ])

    sent_admin = False
    try:
        if ADMIN_ID:
            await bot.send_message(ADMIN_ID, info, reply_markup=ikb)
            sent_admin = True
    except TelegramBadRequest:
        sent_admin = False
    except Exception:
        sent_admin = False

    sent_doctor = False
    try:
        if DOCTOR_ID:
            await bot.send_message(DOCTOR_ID, info, reply_markup=ikb)
            sent_doctor = True
    except TelegramBadRequest:
        sent_doctor = False
    except Exception:
        sent_doctor = False

    # Always inform the user that their question was received locally even if admin delivery failed.
    if sent_admin or sent_doctor:
        await answer_with_sticker(
            message,
            "✅ Savolingiz yuborildi. Javob tez orada keladi.",
            sticker_file_id=STICKER_TARIFF,
            reply_markup=get_menu_for(message.from_user.id)
        )
    else:
        # log not available here; still confirm to user but warn about delivery
        await answer_with_sticker(
            message,
            "✅ Savolingiz qabul qilindi. Hozircha admin yoki doktorga yetkazib bo‘lmadi — tez orada tekshirib qaytaramiz.",
            sticker_file_id=STICKER_TARIFF,
            reply_markup=get_menu_for(message.from_user.id)
        )

    await state.clear()
    session.close()
