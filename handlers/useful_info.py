from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from loader import answer_with_sticker
from config import STICKER_TARIFF
from database import get_user_by_tg, get_user_bonus, set_user_bonus, has_claimed_free_useful, mark_claimed_free_useful

router = Router()


@router.message(lambda m: m.text in ["📚 Foydali ma`lumotlar olish", "Foydali ma`lumotlar olish"])
async def useful_info(message: Message, state: FSMContext | None = None):
    # clear any running FSM so menu buttons aren't intercepted
    try:
        await state.clear()
    except Exception:
        pass

    user = get_user_by_tg(message.from_user.id)
    has_free = False
    if user is not None:
        has_free = has_claimed_free_useful(user.id)

    text = (
        "ℹ️ *Foydali ma'lumotlar obunasi*\n\n"
        "💰 Narxlar:\n"
        "• 1 haftalik: 9 000 so‘m\n"
        "• 1 oylik: 29 000 so‘m\n\n"
        "📌 Bu obunani sotib olishingiz siz uchun juda muhim, "
        "chunki har kuni sizga 'Juda muhim va foydali' ma'lumotlar yuboriladi."
    )

    kb = ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True)
    if not has_free:
        kb.keyboard.append([KeyboardButton(text="1 haftalik obunani tekin olish")])
    kb.keyboard.append([KeyboardButton(text="1 haftalik obuna"), KeyboardButton(text="1 oylik obuna")])
    kb.keyboard.append([KeyboardButton(text="Bosh menuga qaytish")])

    await answer_with_sticker(
        message,
        text + ("\n\nSiz tekin 1 haftalik obunani olishingiz mumkin (bir marta)." if not has_free else ""),
        sticker_file_id=STICKER_TARIFF,
        reply_markup=kb
    )


@router.message(lambda m: m.text in ["1 haftalik obunani tekin olish", "1 haftalik obunani tekin olish"])
async def get_free_week(message: Message):
    user = get_user_by_tg(message.from_user.id)
    if not user:
        await answer_with_sticker(message, "❗ Iltimos, avval ro'yxatdan o'ting.", sticker_file_id=STICKER_TARIFF)
        return
    if has_claimed_free_useful(user.id):
        await answer_with_sticker(message, "❌ Siz allaqachon tekin 1 haftalik obunani olgansiz.", sticker_file_id=STICKER_TARIFF)
        return

    # Mark claimed and inform user. Actual subscriber flow (sending tips) is out of scope here.
    try:
        mark_claimed_free_useful(user.id)
    except Exception:
        pass

    await answer_with_sticker(message, "✅ Sizga 1 haftalik 'Foydali ma'lumotlar' obunasi tekin faollashtirildi!\n\nTarifni to'liq faollashtirish uchun 'Tarif sotib olish' tugmasini bosing.", sticker_file_id=STICKER_TARIFF)


@router.message(lambda m: m.text in ["1 haftalik obuna", "1 haftalik obuna"])
async def buy_week(message: Message, state: FSMContext):
    from handlers.purchase import start_purchase
    try:
        await state.clear()
    except Exception:
        pass
    await start_purchase(message, state, tariff_name="1 haftalik obuna")


@router.message(lambda m: m.text in ["1 oylik obuna", "1 oylik obuna"])
async def buy_month(message: Message, state: FSMContext):
    from handlers.purchase import start_purchase
    try:
        await state.clear()
    except Exception:
        pass
    await start_purchase(message, state, tariff_name="1 oylik obuna")
