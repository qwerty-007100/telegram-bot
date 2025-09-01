# handlers/my_tariff.py
from aiogram import Router
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from loader import answer_with_sticker, bot
from config import STICKER_TARIFF, ADMIN_ID
from database import get_user_by_tg, get_user_bonus, get_referral_counts
import random

router = Router()


# Keyboard shown when user has bonus funds
bonus_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Tarif sotib olish uchun ishlatish")],
        [KeyboardButton(text="Klinika xizmatlari uchun ishlatish")],
        [KeyboardButton(text="Bosh menuga qaytish")]
    ],
    resize_keyboard=True
)


from aiogram.fsm.context import FSMContext


@router.message(lambda m: m.text in ["🧾 Mening tarifim", "Mening tarifim"])
async def my_tariff(message: Message, state: FSMContext):
    # ensure any previous FSM state is cleared so this command is processed cleanly
    try:
        await state.clear()
    except Exception:
        pass
    user = get_user_by_tg(message.from_user.id)
    if not user:
        await answer_with_sticker(message, "❗ Iltimos, avval ro'yxatdan o'ting.", sticker_file_id=STICKER_TARIFF)
        return

    bonus = int(get_user_bonus(user.id) or 0)
    refs = get_referral_counts(user.id)

    text = (
        f"📄 *Sizning tarifingiz:*\n"
        f"🔹 Tarif: {user.tariff or 'Bepul (2 ta savol)'}\n"
        f"📅 Faollashgan sana: {user.tariff_start or '—'}\n"
        f"📅 Tugash sanasi: {user.tariff_end or '—'}\n\n"
        f"💬 Qolgan savollar:\n"
        f"- Kunlik: {user.daily_remaining or 0}\n"
        f"- Haftalik: {user.weekly_remaining or 0}\n"
        f"- Oylik: {user.monthly_remaining or 0}\n\n"
        f"👥 Referal tizim:\n"
    f"- Qo‘shgan odamlar: {refs.get('added', 0)}\n"
    f"- Ro‘yxatdan o‘tganlar: {refs.get('registered', 0)}\n\n"
        f"💰 Bonus mablag‘: {bonus:,} so‘m\n"
    )

    await answer_with_sticker(
        message,
        text,
        sticker_file_id=STICKER_TARIFF,
        parse_mode="Markdown",
        reply_markup=bonus_keyboard if bonus > 0 else None
    )


from keyboards import main_menu_keyboard


@router.message(lambda m: m.text in ["Tarif sotib olish uchun ishlatish", "Tarif sotib olish uchun ishlatish"])
async def use_for_tariff(message: Message, state: FSMContext):
    try:
        await state.clear()
    except Exception:
        pass
    # Directly start purchase flow
    from handlers import purchase
    await purchase.start_purchase(message, state)


@router.message(lambda m: m.text == "Klinika xizmatlari uchun ishlatish")
async def use_for_clinic(message: Message, state: FSMContext):
    try:
        await state.clear()
    except Exception:
        pass
    user = get_user_by_tg(message.from_user.id)
    if not user:
        await answer_with_sticker(message, "❗ Iltimos, avval ro'yxatdan o'ting.", sticker_file_id=STICKER_TARIFF)
        return

    bonus = int(get_user_bonus(user.id) or 0)
    if bonus <= 0:
        await answer_with_sticker(message, "⚠ Sizda bonus mablag‘ mavjud emas.", sticker_file_id=STICKER_TARIFF)
        return

    promo_code = ''.join(random.choices('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=6))
    user_text = (
        f"🏥 Siz klinika xizmatlari uchun bonus mablag‘ingizni ishlatdingiz.\n"
        f"👤 Ism: {user.full_name}\n"
        f"📞 Telefon: {user.phone or '—'}\n"
        f"💳 Bonus: {bonus:,} so‘m\n"
        f"🔑 Promo kod: {promo_code}\n\n"
        f"Ushbu kodni klinikada taqdim eting."
    )
    await answer_with_sticker(message, user_text, sticker_file_id=STICKER_TARIFF)

    admin_text = (
        f"📢 *Klinika bonusi ishlatildi*\n\n"
        f"👤 Ism: {user.full_name}\n"
        f"📞 Telefon: {user.phone or '—'}\n"
        f"🔑 Promo kod: {promo_code}\n"
        f"💳 Bonus: {bonus:,} so‘m"
    )
    if ADMIN_ID:
        await bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown")
