# handlers/purchase.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ContentType
from loader import bot, answer_with_sticker
from config import ADMIN_ID, STICKER_TARIFF
from database import (
    create_pending_payment, get_pending_payment,
    update_pending_payment, activate_tariff, get_user_by_tg
)

router = Router()

# --- Tariflar ro‘yxati ---
TARIFFS = {
    "pro": {"price": 59000, "days": 30, "name": "Pro (oylik)"},
    "premium": {"price": 149000, "days": 30, "name": "Premium (oylik)"},
    "pregnancy": {"price": 499000, "days": 280, "name": "Homiladorlik (9 oy)"},
    "planning": {"price": 199000, "days": 30, "name": "Farzand rejalashtirish (oylik)"}
}


# --- Tarif sotib olish tugmasi ---
@router.message(lambda m: m.text in ["Tarif sotib olish", "🏷 Tarif sotib olish"])
async def choose_tariff(message: Message):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{info['name']} - {info['price']:,} so‘m", callback_data=f"buy:{code}")]
            for code, info in TARIFFS.items()
        ]
    )
    await answer_with_sticker(
        message,
        "💳 Iltimos, tarifni tanlang:",
        sticker_file_id=STICKER_TARIFF,
        reply_markup=kb
    )


# --- Tarif tanlangandan keyin ---
@router.callback_query(F.data.startswith("buy:"))
async def process_buy_callback(call: CallbackQuery):
    code = call.data.split(":")[1]
    tariff = TARIFFS.get(code)
    if not tariff:
        await call.answer("❌ Tarif topilmadi!", show_alert=True)
        return

    payload = {
        "user_tg": call.from_user.id,
        "tariff": code,
        "plan": tariff["name"],
        "base_price": tariff["price"],
        "bonus_applied": 0,
        "payable": tariff["price"],
    }
    pid = create_pending_payment(payload)

    await call.message.answer(
        f"📌 Siz *{tariff['name']}* tarifini tanladingiz.\n\n"
        f"💰 Narxi: {tariff['price']:,} so‘m\n\n"
        f"🧾 Iltimos, to‘lovni amalga oshiring va chekni yuboring.\n"
        f"(To‘lov ID: {pid})",
        parse_mode="Markdown"
    )
    await call.answer()


# --- Foydalanuvchi chek yuborganda ---
@router.message(F.content_type == ContentType.PHOTO)
async def handle_receipt(message: Message):
    user = get_user_by_tg(message.from_user.id)
    if not user:
        await message.answer("❌ Avval ro‘yxatdan o‘ting.")
        return

    # So‘nggi pending paymentni olish
    from sqlalchemy.orm import Session
    from database import SessionLocal, PendingPayment

    session = SessionLocal()
    pp = (
        session.query(PendingPayment)
        .filter(PendingPayment.user_tg == message.from_user.id, PendingPayment.status == "awaiting_receipt")
        .order_by(PendingPayment.created_at.desc())
        .first()
    )

    if not pp:
        await message.answer("❌ Sizning aktiv to‘lovingiz topilmadi.")
        session.close()
        return

    pp.receipt_file_id = message.photo[-1].file_id
    pp.status = "under_review"
    session.commit()
    session.close()

    # Admin ko‘rishi uchun yuboramiz
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"approve:{pp.id}"),
                InlineKeyboardButton(text="❌ Rad etish", callback_data=f"decline:{pp.id}")
            ]
        ]
    )

    await bot.send_photo(
        chat_id=ADMIN_ID,
        photo=message.photo[-1].file_id,
        caption=f"🧾 Yangi to‘lov!\n\nUser: {user.full_name}\nTarif: {pp.plan}\nNarxi: {pp.payable:,} so‘m\n\nID: {pp.id}",
        reply_markup=kb
    )

    await message.answer("✅ Chekingiz qabul qilindi. Admin tasdiqlashini kuting.")


# --- Admin tasdiqlasa ---
@router.callback_query(F.data.startswith("approve:"))
async def approve_payment(call: CallbackQuery):
    pid = int(call.data.split(":")[1])
    payment = get_pending_payment(pid)
    if not payment:
        await call.answer("❌ To‘lov topilmadi.", show_alert=True)
        return

    update_pending_payment(pid, {"status": "approved", "approved_at": dt.datetime.utcnow()})

    # Tarif faollashtirish
    user = get_user_by_tg(payment["user_tg"])
    activate_tariff(user.id, payment["tariff"], TARIFFS[payment["tariff"]]["days"])

    await call.message.edit_caption(call.message.caption + "\n\n✅ Tasdiqlandi!")
    await bot.send_message(payment["user_tg"], "🎉 To‘lovingiz tasdiqlandi! Tarifingiz faollashtirildi ✅")
    await call.answer("Tasdiqlandi ✅")


# --- Admin rad etsa ---
@router.callback_query(F.data.startswith("decline:"))
async def decline_payment(call: CallbackQuery):
    pid = int(call.data.split(":")[1])
    payment = get_pending_payment(pid)
    if not payment:
        await call.answer("❌ To‘lov topilmadi.", show_alert=True)
        return

    update_pending_payment(pid, {"status": "declined", "declined_at": dt.datetime.utcnow()})
    await call.message.edit_caption(call.message.caption + "\n\n❌ Rad etildi!")
    await bot.send_message(payment["user_tg"], "❌ Kechirasiz, to‘lovingiz rad etildi. Iltimos, Adminga murojat qiling.")
    await call.answer("Rad etildi ❌")


# Backwards-compatible export for handlers.payments
try:
    pay_link_kb  # pragma: no cover
except NameError:
    pay_link_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Pay", url="https://example.com/pay")]
    ])

# expose in __all__ if present
if "__all__" in globals():
    __all__.append("pay_link_kb")
else:
    __all__ = ["pay_link_kb"]
