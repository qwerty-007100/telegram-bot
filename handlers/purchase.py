# handlers/purchase.py
import datetime as dt
from aiogram import Router, F, types
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from database import (
    create_pending_payment,
    update_pending_payment,
    get_latest_pending_by_user,
    activate_tariff,
    get_user_by_tg,
    get_pending_payment,
    set_user_bonus,
)
from config import ADMIN_ID
from keyboards import get_menu_for
from loader import answer_with_sticker
from config import STICKER_TARIFF
import logging

logger = logging.getLogger(__name__)

router = Router()

# --- FSM states ---
class PurchaseFSM(StatesGroup):
    choose_tariff = State()
    choose_plan = State()
    confirm_payment = State()
    confirm_bonus = State()
    upload_receipt = State()
    enter_last4 = State()


# --- Keyboards ---
tariff_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Pro"), KeyboardButton(text="Premium")],
        [KeyboardButton(text="Homiladorlik"), KeyboardButton(text="Farzand ko‘rishni rejalashtirish")],
        [KeyboardButton(text="Orqaga")]
    ],
    resize_keyboard=True
)

plan_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="1 haftalik"), KeyboardButton(text="1 oylik")],
        [KeyboardButton(text="Orqaga")]
    ],
    resize_keyboard=True
)

# We will use inline keyboards for plan selection so users must press a button;
# text messages while in the choose_plan state will be ignored.


def make_plan_inline_kb_for(tariff_internal: str) -> InlineKeyboardMarkup:
    """Return an InlineKeyboardMarkup with plan buttons for the given tariff.

    callback_data values follow the requested format, e.g. 'pro_1week', 'premium_1month', etc.
    """
    rows = []
    if tariff_internal == "pro":
        rows.append([
            InlineKeyboardButton(text="1 haftalik", callback_data="pro_1week"),
            InlineKeyboardButton(text="1 oylik", callback_data="pro_1month"),
        ])
    elif tariff_internal == "premium":
        rows.append([
            InlineKeyboardButton(text="1 haftalik", callback_data="premium_1week"),
            InlineKeyboardButton(text="1 oylik", callback_data="premium_1month"),
        ])
    elif tariff_internal == "pregnancy":
        rows.append([
            InlineKeyboardButton(text="Homiladorlik 1 oy", callback_data="homiladorlik_1month"),
            InlineKeyboardButton(text="Homiladorlik 9 oy", callback_data="homiladorlik_9month"),
        ])
    elif tariff_internal == "farzand ko‘rishni rejalashtirish":
        rows.append([
            InlineKeyboardButton(text="1 haftalik", callback_data="farzand_1week"),
            InlineKeyboardButton(text="1 oylik", callback_data="farzand_1month"),
        ])
    else:
        # fallback: offer common plans
        rows.append([
            InlineKeyboardButton(text="1 haftalik", callback_data=f"{tariff_internal}_1week"),
            InlineKeyboardButton(text="1 oylik", callback_data=f"{tariff_internal}_1month"),
        ])

    return InlineKeyboardMarkup(inline_keyboard=rows)

confirm_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Bonus mablag’dan foydalanish"), KeyboardButton(text="Sotib olish")],
        [KeyboardButton(text="Orqaga")]
    ],
    resize_keyboard=True
)


# After instructing for payment, show these buttons: user can say they've paid or go back
post_payment_kb = ReplyKeyboardMarkup(
    keyboard=[
    [KeyboardButton(text="Bekor qilish"), KeyboardButton(text="Tariflar bo'limiga qaytish")]
    ],
    resize_keyboard=True
)


# --- Start purchase ---
@router.message(lambda m: m.text in ["🏷 Tarif sotib olish", "Tarif sotib olish"])
async def start_purchase(msg: types.Message, state: FSMContext, tariff_name: str = None):
    # If tariff_name is provided, preselect and advance to plan selection
    if tariff_name:
        # normalize and set tariff so next user plan selection is validated
        t = str(tariff_name).lower()
        # map user-friendly names to internal tariff keys
        if "1 haftalik obuna" in t or "1 oylik obuna" in t:
            # keep using reply keyboard for the friendly 'useful' subscription flows
            await state.update_data(tariff=t, require_inline=False)
            await state.set_state(PurchaseFSM.choose_plan)
            await msg.answer("Qaysi reja kerak?", reply_markup=plan_kb)
            return
        elif "pro" in t:
            await state.update_data(tariff="pro", require_inline=True)
            await state.set_state(PurchaseFSM.choose_plan)
            kb = make_plan_inline_kb_for("pro")
            await msg.answer("Qaysi reja kerak?", reply_markup=kb)
            return
        elif "premium" in t:
            await state.update_data(tariff="premium", require_inline=True)
            await state.set_state(PurchaseFSM.choose_plan)
            kb = make_plan_inline_kb_for("premium")
            await msg.answer("Qaysi reja kerak?", reply_markup=kb)
            return
        elif "homiladorlik" in t:
            await state.update_data(tariff="pregnancy", require_inline=True)
            await state.set_state(PurchaseFSM.choose_plan)
            kb = make_plan_inline_kb_for("pregnancy")
            await msg.answer("Homiladorlik uchun reja tanlang:", reply_markup=kb)
            return
        elif "farzand" in t:
            await state.update_data(tariff="farzand ko‘rishni rejalashtirish", require_inline=True)
            await state.set_state(PurchaseFSM.choose_plan)
            kb = make_plan_inline_kb_for("farzand ko‘rishni rejalashtirish")
            await msg.answer("Qaysi reja kerak?", reply_markup=kb)
            return

    # No preselected tariff: show overview and let user pick
    await state.set_state(PurchaseFSM.choose_tariff)
    await answer_with_sticker(
        msg,
        "Tariflar haqida ma'lumot:\n\n"
        "📌 Pro: 1 hafta – 19 000 so‘m, 1 oy – 59 000 so‘m\n"
        "📌 Premium: 1 hafta – 29 000 so‘m, 1 oy – 99 000 so‘m\n"
        "📌 Homiladorlik: 1 oy – 79 000 so‘m, 9 oy – 349 000 so‘m\n"
        "📌 Farzand ko‘rishni rejalashtirish: 1 hafta – 59 000 so‘m, 1 oy – 199 000 so‘m\n\n"
        "Qaysi tarifni sotib olmoqchisiz?",
        sticker_file_id=STICKER_TARIFF,
        reply_markup=tariff_kb
    )


# --- Tariff chosen ---
@router.message(PurchaseFSM.choose_tariff)
async def choose_tariff(msg: types.Message, state: FSMContext):
    text = msg.text.lower()
    if text in ["pro", "premium", "farzand ko‘rishni rejalashtirish"]:
        await state.update_data(tariff=text, require_inline=True)
        await state.set_state(PurchaseFSM.choose_plan)
        # send inline buttons for plan selection
        kb = make_plan_inline_kb_for(text)
        await msg.answer("Qaysi reja kerak?", reply_markup=kb)
    elif text == "homiladorlik":
        await state.update_data(tariff="pregnancy", require_inline=True)
        await state.set_state(PurchaseFSM.choose_plan)
        kb = make_plan_inline_kb_for("pregnancy")
        await msg.answer("Homiladorlik uchun reja tanlang:", reply_markup=kb)
    else:
        # Only trigger this message when user is inside purchase FSM and sent an invalid option
        await msg.answer("❌ Iltimos, mavjud tariflar orasidan tanlang yoki 'Orqaga' tugmasi bilan qayting.")


@router.callback_query(lambda c: c.data and (
    c.data.startswith("pro_") or c.data.startswith("premium_") or
    c.data.startswith("homiladorlik_") or c.data.startswith("farzand_") or
    c.data.startswith("1 haftalik obuna_") or c.data.startswith("1 oylik obuna_")
))
async def plan_callback(callback: types.CallbackQuery, state: FSMContext):
    """Handle inline plan selection callbacks (e.g. 'pro_1week').

    Creates a pending payment, stores it in FSM data and advances to confirm state.
    """
    data = callback.data or ""
    mapping = {
        "pro_1week": ("pro", "1 haftalik"),
        "pro_1month": ("pro", "1 oylik"),
        "premium_1week": ("premium", "1 haftalik"),
        "premium_1month": ("premium", "1 oylik"),
        "homiladorlik_1month": ("pregnancy", "homiladorlik 1 oy"),
        "homiladorlik_9month": ("pregnancy", "homiladorlik 9 oy"),
        "farzand_1week": ("farzand ko‘rishni rejalashtirish", "1 haftalik"),
        "farzand_1month": ("farzand ko‘rishni rejalashtirish", "1 oylik"),
    }

    if data not in mapping:
        return

    tariff, plan = mapping[data]

    prices = {
        ("pro", "1 haftalik"): 19000,
        ("pro", "1 oylik"): 59000,
        ("premium", "1 haftalik"): 29000,
        ("premium", "1 oylik"): 99000,
        ("pregnancy", "homiladorlik 1 oy"): 79000,
        ("pregnancy", "homiladorlik 9 oy"): 349000,
        ("farzand ko‘rishni rejalashtirish", "1 haftalik"): 59000,
        ("farzand ko‘rishni rejalashtirish", "1 oylik"): 199000,
        ("1 haftalik obuna", "1 haftalik"): 9000,
        ("1 oylik obuna", "1 oylik"): 29000,
    }

    price = prices.get((tariff, plan)) or prices.get((str(tariff).lower(), plan))
    if not price:
        try:
            await callback.answer(text="❌ Xatolik: reja topilmadi.", show_alert=True)
        except Exception:
            pass
        return

    payload = {
        "user_tg": callback.from_user.id,
        "tariff": tariff,
        "plan": plan,
        "base_price": price,
        "payable": price,
    }
    pid = create_pending_payment(payload)
    await state.update_data(payment_id=pid, tariff=tariff, plan=plan)

    await state.set_state(PurchaseFSM.confirm_payment)
    try:
        await callback.answer()
    except Exception:
        pass

    await callback.message.answer(
        f"✅ Siz tanladingiz:\nTarif: {tariff}\nReja: {plan}\nNarx: {price} so‘m\n\n"
        "To‘lov turini tanlang:",
        reply_markup=confirm_kb
    )


@router.message(PurchaseFSM.choose_plan)
async def choose_plan(msg: types.Message, state: FSMContext):
    """Backward-compatible function: accept textual plan selection from reply keyboard.

    This allows older handlers (e.g. `handlers.tariffs.plan_selected`) to delegate to
    `choose_plan(msg, state)` when they still use reply keyboards.
    """
    text = (msg.text or "").strip()
    text_map = {
        "1 haftalik": "_1week",
        "1 oylik": "_1month",
        "homiladorlik 1 oy": "_1month",
        "homiladorlik 9 oy": "_9month",
    }

    # DEBUG: show FSM data for troubleshooting (remove in production)
    data = await state.get_data()
    try:
        await msg.answer(f"DEBUG: current state data: {data}")
    except Exception:
        pass
    tariff = data.get("tariff")
    if not tariff:
        # If tariff not set, try to infer from context (not ideal)
        await msg.answer("Iltimos, avval tarifni tanlang.")
        return

    suffix = text_map.get(text.lower())
    if not suffix:
        await msg.answer("❌ Noto'g'ri reja tanlandi, qaytadan urinib ko'ring.")
        return

    # build callback-like key
    # normalize tariff to key used in mapping
    # Special-case the 'useful' subscription friendly keys stored like '1 haftalik obuna'
    if str(tariff).lower().startswith("1 haftalik obuna") or str(tariff).lower().startswith("1 oylik obuna"):
        # treat these as their own tariff keys
        if text.lower() == "1 haftalik":
            key = "1 haftalik obuna_1week"
        else:
            key = "1 oylik obuna_1month"
    else:
        tkey = tariff
        if tariff == "pregnancy":
            key = f"homiladorlik{text_map[text.lower()] }"
        else:
            # map 'farzand ko‘rishni rejalashtirish' to 'farzand'
            short = "farzand" if "farzand" in str(tariff).lower() else tariff
            key = f"{short}{text_map[text.lower()] }"

    # reuse mapping from callback handler
    mapping = {
        "pro_1week": ("pro", "1 haftalik"),
        "pro_1month": ("pro", "1 oylik"),
        "premium_1week": ("premium", "1 haftalik"),
        "premium_1month": ("premium", "1 oylik"),
        "homiladorlik_1month": ("pregnancy", "homiladorlik 1 oy"),
        "homiladorlik_9month": ("pregnancy", "homiladorlik 9 oy"),
        "farzand_1week": ("farzand ko‘rishni rejalashtirish", "1 haftalik"),
        "farzand_1month": ("farzand ko‘rishni rejalashtirish", "1 oylik"),
    # friendly useful subscription mapping
    "1 haftalik obuna_1week": ("1 haftalik obuna", "1 haftalik"),
    "1 oylik obuna_1month": ("1 oylik obuna", "1 oylik"),
    }

    # try to find the exact mapping key
    # If tariff is 'pro' or 'premium' use those; else try pregnancy/farzand
    possible_keys = []
    if tariff in ("pro", "premium"):
        if text.lower() == "1 haftalik":
            possible_keys.append(f"{tariff}_1week")
        else:
            possible_keys.append(f"{tariff}_1month")
    elif tariff == "pregnancy":
        if "9" in text:
            possible_keys.append("homiladorlik_9month")
        else:
            possible_keys.append("homiladorlik_1month")
    else:
        # assume farzand
        if text.lower() == "1 haftalik":
            possible_keys.append("farzand_1week")
        else:
            possible_keys.append("farzand_1month")

    found = None
    for k in possible_keys:
        if k in mapping:
            found = mapping[k]
            break

    if not found:
        await msg.answer("❌ Xatolik: reja topilmadi.")
        return

    tariff, plan = found

    # price lookup (same table as callback)
    prices = {
        ("pro", "1 haftalik"): 19000,
        ("pro", "1 oylik"): 59000,
        ("premium", "1 haftalik"): 29000,
        ("premium", "1 oylik"): 99000,
        ("pregnancy", "homiladorlik 1 oy"): 79000,
        ("pregnancy", "homiladorlik 9 oy"): 349000,
        ("farzand ko‘rishni rejalashtirish", "1 haftalik"): 59000,
        ("farzand ko‘rishni rejalashtirish", "1 oylik"): 199000,
        # Useful subscription friendly keys
        ("1 haftalik obuna", "1 haftalik"): 9000,
        ("1 oylik obuna", "1 oylik"): 29000,
    }

    price = prices.get((tariff, plan))
    if not price:
        price = prices.get((str(tariff).lower(), plan))

    if not price:
        await msg.answer("❌ Xatolik: reja topilmadi.")
        return

    payload = {
        "user_tg": msg.from_user.id,
        "tariff": tariff,
        "plan": plan,
        "base_price": price,
        "payable": price,
    }
    pid = create_pending_payment(payload)
    await state.update_data(payment_id=pid, tariff=tariff, plan=plan)

    await state.set_state(PurchaseFSM.confirm_payment)
    await msg.answer(
        f"✅ Siz tanladingiz:\nTarif: {tariff}\nReja: {plan}\nNarx: {price} so‘m\n\n"
        "To‘lov turini tanlang:",
        reply_markup=confirm_kb
    )


# --- Confirm payment ---
@router.message(PurchaseFSM.confirm_payment)
async def confirm_payment(msg: types.Message, state: FSMContext):
    """Handle user's choice after a plan is selected: either use bonus or pay normally.

    Use fuzzy matching to accept minor text variants and ensure we don't override
    the `confirm_bonus` state with `upload_receipt`.
    """
    data = await state.get_data()
    pid = data.get("payment_id")

    text = (msg.text or "").strip().lower()
    # normalize common apostrophes/quotes
    norm = text.replace("’", "'").replace("`", "'")

    # Detect bonus intent (accept variants)
    if "bonus" in norm and ("foyd" in norm or "mablag" in norm or "foydalan" in norm):
        pp = get_latest_pending_by_user(msg.from_user.id)
        if not pp:
            await msg.answer("Xatolik yuz berdi.")
            return
        # use actual bonus balance from DB
        user_db = get_user_by_tg(msg.from_user.id)
        bonus_available = int(getattr(user_db, "bonus_balance", 0) or 0)
        if bonus_available <= 0:
            await msg.answer("⚠ Sizda bonus mablag‘ mavjud emas.")
            return
        bonus_to_apply = min(bonus_available, int(pp.get("base_price", 0)))
        new_payable = max(0, int(pp["base_price"]) - int(bonus_to_apply))

        # store bonus decision in FSM data and ask confirmation
        await state.update_data(payment_id=pid, bonus_to_apply=int(bonus_to_apply), new_payable=int(new_payable))
        await state.set_state(PurchaseFSM.confirm_bonus)

        # confirmation keyboard (reply keyboard so user can press Ha/Yo'q)
        from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
        confirm_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Ha"), KeyboardButton(text="Yo'q")]], resize_keyboard=True)

        await msg.answer(
            f"Tarif narxi: {pp['base_price']} so‘m\n"
            f"Bonus: {int(bonus_to_apply)} so‘m\n"
            f"Siz to‘laysiz: {new_payable} so‘m\n\n"
            "Bonus mablag‘ini ishlatmoqchimisiz?",
            reply_markup=confirm_kb
        )
        return

    # Detect pay intent (accept variants like 'sotib', 'sotib olish')
    if "sotib" in norm or "to'lov" in norm or "tolov" in norm:
        pp = get_latest_pending_by_user(msg.from_user.id)
        if not pp:
            await msg.answer("Xatolik yuz berdi.")
            return
        await msg.answer(
            f"Tarif narxi: {pp['base_price']} so‘m\n"
            "9860 0101 0114 6065 (Botirov B.) kartasiga to‘lovni amalga oshiring.",
        )

        # move into upload_receipt and ask for receipt
        await state.set_state(PurchaseFSM.upload_receipt)
        await answer_with_sticker(msg, "✅ To‘lovni amalga oshirgach, chek yoki screenshotni yuboring.", sticker_file_id=STICKER_TARIFF, reply_markup=post_payment_kb)
        return

    # Unknown reply in confirm state
    await msg.answer("Iltimos, 'Bonus mablag’dan foydalanish' yoki 'Sotib olish' tugmasini bosing.")



@router.message(PurchaseFSM.confirm_bonus)
async def handle_confirm_bonus(msg: types.Message, state: FSMContext):
    """Handle user's confirmation to use bonus balance for the pending payment."""
    text = (msg.text or "").strip().lower()
    # normalize common variants
    norm = text.replace("'", "").replace("’", "")
    # fetch FSM data
    data = await state.get_data()
    pid = data.get("payment_id")
    bonus_to_apply = int(data.get("bonus_to_apply") or 0)
    new_payable = int(data.get("new_payable") or 0)

    if norm.startswith("ha"):
        # apply bonus: mark pending payment approved and deduct bonus, then activate tariff immediately
        pp = get_pending_payment(pid)
        if not pp:
            await msg.answer("Xatolik: to'lov topilmadi.")
            await state.clear()
            return
        # Update pending payment with bonus applied and new payable
        update_pending_payment(pid, {"bonus_applied": int(bonus_to_apply), "payable": int(new_payable)})

        user = get_user_by_tg(msg.from_user.id)
        try:
            curr = int(getattr(user, "bonus_balance", 0) or 0)
            if bonus_to_apply and curr >= bonus_to_apply:
                set_user_bonus(user.id, curr - int(bonus_to_apply))
        except Exception:
            pass

        # If bonus does NOT fully cover the price, ask the user to pay the remaining amount and upload receipt
        if int(new_payable) > 0:
            try:
                await msg.answer(
                    f"Tarif narxi: {pp['base_price']} so‘m\n"
                    f"Bonus: {int(bonus_to_apply)} so‘m\n"
                    f"Qolgan summa: {int(new_payable)} so‘m\n\n"
                    "Iltimos, qolgan summani to‘lang va chekni yuboring.",
                    reply_markup=post_payment_kb
                )
            except Exception:
                pass
            # set state to upload_receipt so user can send photo of payment
            await state.set_state(PurchaseFSM.upload_receipt)
            return

        # Bonus covered full price: approve and activate tariff
        update_pending_payment(pid, {"status": "approved", "approved_at": dt.datetime.utcnow(), "payable": 0})

        # determine days from plan then activate tariff
        plan = (pp.get("plan") or "").lower()
        if "haftalik" in plan:
            days = 7
        elif "9 oy" in plan or "9 oy" in pp.get("plan", ""):
            days = 280
        else:
            days = 30

        try:
            activate_tariff(user.id, pp["tariff"], days)
        except Exception:
            pass

        await msg.answer("🎉 Bonus ishlatildi va tarif faollashtirildi!", reply_markup=get_menu_for(msg.from_user.id))
        await state.clear()
        return

    # user declined
    if norm.startswith("yo") or norm.startswith("n"):
        try:
            update_pending_payment(pid, {"status": "declined", "declined_at": dt.datetime.utcnow()})
        except Exception:
            pass
        await msg.answer("❌ To'lov bekor qilindi.", reply_markup=get_menu_for(msg.from_user.id))
        await state.clear()
        return

    # unknown reply -> prompt again
    await msg.answer("Iltimos, 'Ha' yoki 'Yo'q' tugmasini bosing.")


# Global 'Orqaga' handler — always available to let users back out to main menu
@router.message(lambda m: m.text == "Orqaga")
async def global_go_back(msg: types.Message, state: FSMContext):
    await state.clear()
    await msg.answer("Bosh menyuga qaytildi.", reply_markup=get_menu_for(msg.from_user.id))


@router.message(lambda m: m.text == "Bekor qilish")
async def cancel_payment(msg: types.Message, state: FSMContext):
    """Cancel the current payment flow and return to main menu."""
    try:
        await state.clear()
    except Exception:
        pass
    await answer_with_sticker(msg, "❌ To'lov bekor qilindi. Bosh menyuga qaytildi.", sticker_file_id=STICKER_TARIFF, reply_markup=get_menu_for(msg.from_user.id))


# --- Upload receipt ---
@router.message(PurchaseFSM.upload_receipt, F.photo)
async def upload_receipt(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    pid = data.get("payment_id")
    file_id = msg.photo[-1].file_id
    update_pending_payment(pid, {"receipt_file_id": file_id, "status": "under_review"})

    await state.set_state(PurchaseFSM.enter_last4)
    await msg.answer("✅ Endi kartangizning oxirgi 4 ta raqamini yuboring.")


# --- Enter last4 ---
@router.message(PurchaseFSM.enter_last4)
async def enter_last4(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    pid = data.get("payment_id")
    last4 = msg.text.strip()

    # Validate last4: expect exactly 4 digits
    if not last4.isdigit() or len(last4) != 4:
        await msg.answer("Iltimos, kartaning oxirgi 4 ta raqamini faqat raqam sifatida yuboring (masalan: 1234).")
        return

    update_pending_payment(pid, {"payer_last4": last4})

    user = get_user_by_tg(msg.from_user.id)
    pp = get_latest_pending_by_user(msg.from_user.id)

    txt = (
        f"💳 Yangi to‘lov\n\n"
        f"Foydalanuvchi: {user.full_name}\n"
        f"Telefon: {user.phone}\n"
        f"Tarif: {pp['tariff']} {pp['plan']}\n"
        f"Narx: {pp['base_price']} so‘m\n"
        f"Bonus: {pp['bonus_applied']} so‘m\n"
        f"To‘lov: {pp['payable']} so‘m\n"
        f"Karta oxirgi 4 raqami: {last4}"
    )

    # Send receipt with inline approve/decline buttons to admin and doctor (if configured)
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    ikb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Tasdiqlash", callback_data=f"approve_{pid}"),
            InlineKeyboardButton(text="To'lovni rad qilish", callback_data=f"decline_{pid}")
        ]
    ])

    # send to admin
    try:
        await msg.bot.send_photo(ADMIN_ID, pp["receipt_file_id"], caption=txt, reply_markup=ikb)
    except Exception:
        pass
    # send to doctor if configured
    try:
        from config import DOCTOR_ID
        if DOCTOR_ID:
            await msg.bot.send_photo(DOCTOR_ID, pp["receipt_file_id"], caption=txt, reply_markup=ikb)
    except Exception:
        pass
    await msg.answer(
        "✅ To‘lovingiz adminga yuborildi. 10-15 daqiqa ichida javob beriladi.",
        reply_markup=get_menu_for(msg.from_user.id)
    )
    await state.clear()


# If user clicks the 'To'lov qildim' button outside photo flow, prompt them to upload receipt
@router.message(lambda m: m.text == "To'lov qildim")
async def i_paid(msg: types.Message, state: FSMContext):
    await answer_with_sticker(msg, "Iltimos, chek yoki to‘lov screenshotini shu chatga yuboring.", sticker_file_id=STICKER_TARIFF)
    await state.set_state(PurchaseFSM.upload_receipt)


# If user wants to return to tariffs list
@router.message(lambda m: m.text == "Tariflar bo'limiga qaytish")
async def back_to_tariffs(msg: types.Message, state: FSMContext):
    await state.clear()
    from handlers.tariffs import buy_tariff
    await buy_tariff(msg, state)


# --- Admin confirm/decline ---
@router.message(F.text.startswith("Tasdiqlash:"))
async def approve_payment(msg: types.Message):
    pid = int(msg.text.split(":")[1])
    # mark approved
    update_pending_payment(pid, {"status": "approved", "approved_at": dt.datetime.utcnow()})

    pp = get_pending_payment(pid)
    if not pp:
        await msg.answer("Xatolik: to'lov topilmadi.")
        return

    user = get_user_by_tg(pp["user_tg"])
    if not user:
        await msg.answer("Xatolik: foydalanuvchi topilmadi.")
        return

    # determine days
    plan = (pp.get("plan") or "").lower()
    if "haftalik" in plan:
        days = 7
    elif "9 oy" in plan or "9 oy" in pp.get("plan", ""):
        days = 280
    else:
        days = 30

    activate_tariff(user.id, pp["tariff"], days)

    # deduct bonus used
    try:
        bonus_used = int(pp.get("bonus_applied") or 0)
        if bonus_used and getattr(user, "bonus_balance", 0) >= bonus_used:
            set_user_bonus(user.id, int(getattr(user, "bonus_balance", 0)) - bonus_used)
    except Exception:
        pass

    await msg.answer("✅ To‘lov tasdiqlandi va tarif faollashtirildi.")


@router.message(F.text.startswith("Bekor qilish:"))
async def decline_payment(msg: types.Message):
    pid = int(msg.text.split(":")[1])
    update_pending_payment(pid, {"status": "declined", "declined_at": dt.datetime.utcnow()})
    await msg.answer("❌ To‘lov bekor qilindi. Iltimos, sababini bilish uchun adminga murojat qiling.")


@router.callback_query(lambda c: c.data and (c.data.startswith("approve_") or c.data.startswith("approve:")))
async def cb_approve(call: types.CallbackQuery):
    # only admin/doctor can approve
    uid = call.from_user.id
    from config import ADMIN_ID, DOCTOR_ID
    if uid not in (ADMIN_ID, DOCTOR_ID):
        try:
            await call.answer("⛔ Sizda ruxsat yo'q", show_alert=True)
        except Exception:
            pass
        return

    # acknowledge quickly to stop loading spinner and log
    try:
        await call.answer()
    except Exception:
        pass
    try:
        logger.info("cb_approve invoked by %s data=%s", uid, call.data)
    except Exception:
        pass

    # support both 'approve_<id>' and 'approve:<id>' formats
    raw = call.data.replace(":", "_")
    try:
        pid = int(raw.split("_")[1])
    except Exception:
        return await call.answer("Xatolik: noto'g'ri to'lov ID.", show_alert=True)
    update_pending_payment(pid, {"status": "approved", "approved_at": dt.datetime.utcnow()})
    pp = get_pending_payment(pid)
    if not pp:
        return await call.answer("Xatolik: to'lov topilmadi.", show_alert=True)

    user = get_user_by_tg(pp["user_tg"])
    if not user:
        return await call.answer("Xatolik: foydalanuvchi topilmadi.", show_alert=True)

    # determine days
    plan = (pp.get("plan") or "").lower()
    if "haftalik" in plan:
        days = 7
    elif "9 oy" in plan or "9 oy" in pp.get("plan", ""):
        days = 280
    else:
        days = 30

    activate_tariff(user.id, pp["tariff"], days)

    # deduct bonus if any
    try:
        bonus_used = int(pp.get("bonus_applied") or 0)
        if bonus_used and getattr(user, "bonus_balance", 0) >= bonus_used:
            set_user_bonus(user.id, int(getattr(user, "bonus_balance", 0)) - bonus_used)
    except Exception:
        pass

    # notify admin in chat (if possible)
    try:
        if call.message:
            await call.message.answer("✅ To‘lov tasdiqlandi va tarif faollashtirildi.")
    except Exception:
        pass
    # notify the user about approval with a short message signed by clinic/doctor
    try:
        sign = "Doctor Mirsaid"
        user_tg = pp.get("user_tg")
        if user_tg:
            await call.bot.send_message(user_tg, f"{sign}: ✅ To'lovingiz tasdiqlandi. Tarif faollashtirildi.")
    except Exception:
        pass
    # final callback acknowledgment (redundant if already answered)
    try:
        await call.answer("Tasdiqlandi", show_alert=False)
    except Exception:
        pass


@router.callback_query(lambda c: c.data and (c.data.startswith("decline_") or c.data.startswith("decline:")))
async def cb_decline(call: types.CallbackQuery):
    uid = call.from_user.id
    from config import ADMIN_ID, DOCTOR_ID
    if uid not in (ADMIN_ID, DOCTOR_ID):
        try:
            await call.answer("⛔ Sizda ruxsat yo'q", show_alert=True)
        except Exception:
            pass
        return

    # ack early and log
    try:
        await call.answer()
    except Exception:
        pass
    try:
        logger.info("cb_decline invoked by %s data=%s", uid, call.data)
    except Exception:
        pass

    raw = call.data.replace(":", "_")
    try:
        pid = int(raw.split("_")[1])
    except Exception:
        try:
            await call.answer("Xatolik: noto'g'ri to'lov ID.", show_alert=True)
        except Exception:
            pass
        return
    update_pending_payment(pid, {"status": "declined", "declined_at": dt.datetime.utcnow()})
    # prepare a clearer admin notification with payment details
    try:
        pp = get_pending_payment(pid)
        user_tg = None
        user_full = "Noma'lum foydalanuvchi"
        if pp:
            user_tg = pp.get("user_tg")
            try:
                user_obj = get_user_by_tg(user_tg) if user_tg else None
                user_full = getattr(user_obj, "full_name", str(user_tg) if user_tg else user_full)
            except Exception:
                pass

        admin_text = (
            "❌ To'lov rad etildi\n\n"
            f"Foydalanuvchi: {user_full}\n"
            f"Tarif: {pp.get('tariff', '-') if pp else '-'} {pp.get('plan', '') if pp else ''}\n"
            f"To'lov ID: {pid}\n\n"
            "Foydalanuvchiga xabar yuborilmoqda..."
        )
        try:
            if call.message:
                await call.message.answer(admin_text)
        except Exception:
            # ignore UI errors for admin chat
            pass
    except Exception:
        pass

    # notify the user about decline with a helpful, signed message and contact button
    try:
        if pp and (user_tg := pp.get("user_tg")):
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            notify_kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Adminga yozish", url="https://t.me/homilayordami")],
                [InlineKeyboardButton(text="Qo'ng'iroq yordam: +998945623111", url="tel:+998945623111")]
            ])
            sign = "Doctor Mirsaid"
            user_text = (
                f"{sign} javobi — ❌ To'lovingiz rad etildi.\n\n"
                "Iltimos, sababini aniqlash uchun admin bilan bog'laning.\n"
                "Agar kerak bo'lsa, to'lovni qayta amalga oshirish yoki boshqa to'lov usulini tanlash mumkin.\n\n"
                "Admin bilan bog'lanish uchun pastdagi tugmani bosing."
            )
            try:
                await call.bot.send_message(user_tg, user_text, reply_markup=notify_kb)
            except Exception:
                pass
    except Exception:
        pass

    try:
        await call.answer("Bekor qilindi", show_alert=False)
    except Exception:
        pass
