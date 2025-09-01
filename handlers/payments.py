"""
handlers/payments.py

Telegram Payments integration (Telegram Payments API) using a Stripe provider token.

Flow:
- User requests to pay (callback "start_pay:{purchase_id}").
- Bot sends an invoice (bot.send_invoice) to the user using provider token from config.
- Telegram performs pre-checkout; bot accepts through built-in handlers.
- When payment is completed, Telegram sends a message with successful_payment:
  - We listen for successful_payment messages and mark the pending payment as approved,
    save provider IDs, activate the user's tariff and notify the user in Uzbek.

Notes:
- Uses existing synchronous DB helpers in database.py:
    create_pending_payment, get_pending_payment, update_pending_payment, activate_tariff
  This keeps storage consistent with the rest of the project (SQLite).
- All user-facing messages go through loader.answer_with_sticker.
- Ensure STRIPE_PROVIDER_TOKEN and PAYMENT_CURRENCY are set in your .env / config.py.
"""

import os
import time
import json
import aiohttp
import datetime as dt
from typing import Optional, List
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, LabeledPrice, PreCheckoutQuery
from loader import answer_with_sticker, bot
from config import STRIPE_PROVIDER_TOKEN, PAYMENT_CURRENCY, STICKER_TARIFF
from database import get_pending_payment, update_pending_payment, create_pending_payment, activate_tariff, get_user_by_tg

from keyboards.inline.purchase import pay_link_kb
from utils.payment import human_name, duration_days

router = Router()

# Helper: build LabeledPrice list for Telegram invoice
def _build_prices(amount: int) -> List[LabeledPrice]:
    """
    Build Telegram LabeledPrice objects.
    amount is an integer in the main currency unit (for UZS you may need to adjust).
    Telegram expects price values as strings representing float in the smallest currency
    unit depending on the currency. For many currencies Telegram expects integer values
    as string representing "major" currency units (e.g., "100.00").
    Here we provide a simple representation "amount" as string (no decimals).
    Adjust as needed for currency specifics.
    """
    # Represent price as string. If provider requires cents, adjust multiplier in config or here.
    return [LabeledPrice(label="To'lov", amount=str(int(amount)))]

# ----- Helper: generate payment link for available providers -----
async def _generate_payment_link(payable: int, label: str, purchase_id: int) -> str:
    """
    Attempt to generate a real payment link using provider credentials from env:
      - STRIPE_API_KEY -> Stripe Checkout Session
      - PAYPAL_CLIENT_ID & PAYPAL_SECRET -> PayPal Order (returns approve link)
      - QIWI_API_KEY -> Qiwi P2P bill (returns payUrl)
    Fallback: returns a safe placeholder link.

    payable: integer amount in "so'm" or provider currency (project uses local currencies).
    label: human-readable label for payment purpose.
    purchase_id: purchase id (for attaching to link).
    """
    # Normalize label and ensure safe characters
    label_safe = label.replace(" ", "_")[:40]

    # 1) Try Stripe Checkout (if STRIPE_API_KEY is set)
    STRIPE_KEY = os.getenv("STRIPE_API_KEY")
    if STRIPE_KEY:
        try:
            # Create a Checkout Session via Stripe API
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {STRIPE_KEY}",
                    "Content-Type": "application/x-www-form-urlencoded"
                }
                # Stripe expects amounts in the smallest currency unit; assume UZS not supported,
                # use a fallback currency param or the raw amount for vendor to adapt.
                data = {
                    "mode": "payment",
                    "success_url": f"https://example.com/pay/success?pid={purchase_id}",
                    "cancel_url": f"https://example.com/pay/cancel?pid={purchase_id}",
                    "line_items[0][price_data][currency]": os.getenv("STRIPE_CURRENCY", "usd"),
                    "line_items[0][price_data][product_data][name]": label_safe,
                    "line_items[0][price_data][unit_amount]": str(int(os.getenv("STRIPE_UNIT_MULTIPLIER", 100)) * int(payable)),
                    "line_items[0][quantity]": "1",
                }
                resp = await session.post("https://api.stripe.com/v1/checkout/sessions", data=data, headers=headers, timeout=15)
                if resp.status in (200, 201):
                    res_json = await resp.json()
                    url = res_json.get("url")
                    if url:
                        return url
        except Exception:
            pass  # best-effort, continue to next provider

    # 2) Try PayPal Orders API (if client id/secret provided)
    PAYPAL_CLIENT = os.getenv("PAYPAL_CLIENT_ID")
    PAYPAL_SECRET = os.getenv("PAYPAL_SECRET")
    PAYPAL_API = os.getenv("PAYPAL_API", "https://api-m.sandbox.paypal.com")  # default to sandbox
    if PAYPAL_CLIENT and PAYPAL_SECRET:
        try:
            async with aiohttp.ClientSession() as session:
                # Get OAuth token
                auth = aiohttp.BasicAuth(PAYPAL_CLIENT, PAYPAL_SECRET)
                token_resp = await session.post(f"{PAYPAL_API}/v1/oauth2/token", data={"grant_type": "client_credentials"}, auth=auth, timeout=10)
                if token_resp.status in (200, 201):
                    token_data = await token_resp.json()
                    access_token = token_data.get("access_token")
                    if access_token:
                        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
                        order_body = {
                            "intent": "CAPTURE",
                            "purchase_units": [
                                {
                                    "amount": {"currency_code": os.getenv("PAYPAL_CURRENCY", "USD"), "value": str(payable)},
                                    "description": label_safe
                                }
                            ],
                            "application_context": {
                                "return_url": f"https://example.com/pay/paypal/success?pid={purchase_id}",
                                "cancel_url": f"https://example.com/pay/paypal/cancel?pid={purchase_id}"
                            }
                        }
                        order_resp = await session.post(f"{PAYPAL_API}/v2/checkout/orders", json=order_body, headers=headers, timeout=15)
                        if order_resp.status in (200, 201):
                            order_json = await order_resp.json()
                            # extract approval link
                            for link in order_json.get("links", []):
                                if link.get("rel") == "approve":
                                    return link.get("href")
        except Exception:
            pass

    # 3) Try Qiwi P2P (if QIWI_API_KEY set)
    QIWI_TOKEN = os.getenv("QIWI_API_KEY")
    QIWI_BASE = os.getenv("QIWI_API_BASE", "https://api.qiwi.com/partner/bill/v1")
    if QIWI_TOKEN:
        try:
            import uuid
            bill_id = str(uuid.uuid4())
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {QIWI_TOKEN}", "Content-Type": "application/json"}
                body = {
                    "amount": {"value": str(payable), "currency": os.getenv("QIWI_CURRENCY", "UZS")},
                    "comment": f"{label_safe} pid:{purchase_id}",
                    "expirationDateTime": None
                }
                resp = await session.put(f"{QIWI_BASE}/bills/{bill_id}", json=body, headers=headers, timeout=10)
                if resp.status in (200, 201):
                    data = await resp.json()
                    pay_url = data.get("payUrl") or data.get("viewUrl")
                    if pay_url:
                        return pay_url
        except Exception:
            pass

    # Fallback placeholder link (safe)
    return f"https://pay.example.com/pay?amount={payable}&pid={purchase_id}&label={label_safe}"


# ----- Helper: attempt to verify payment status -----
async def _verify_payment_by_link(link: str) -> str:
    """
    Try to infer provider from link and verify payment status.
    Returns: "paid", "pending", "failed"
    This is best-effort. If verification cannot be performed, return "pending".
    """
    if not link:
        return "pending"

    # Stripe: session URLs contain "checkout" and query param "session_id" in some flows
    if "stripe.com" in link or "checkout" in link:
        STRIPE_KEY = os.getenv("STRIPE_API_KEY")
        if not STRIPE_KEY:
            return "pending"
        # try to extract session id (very heuristic)
        if "session_id=" in link:
            sid = link.split("session_id=")[-1].split("&")[0]
            try:
                async with aiohttp.ClientSession() as session:
                    headers = {"Authorization": f"Bearer {STRIPE_KEY}"}
                    resp = await session.get(f"https://api.stripe.com/v1/checkout/sessions/{sid}", headers=headers, timeout=10)
                    if resp.status == 200:
                        data = await resp.json()
                        payment_status = data.get("payment_status")
                        if payment_status == "paid":
                            return "paid"
            except Exception:
                return "pending"
        return "pending"

    # PayPal: approval links include "paypal.com" and usually have token/order id as query param
    if "paypal.com" in link:
        PAYPAL_CLIENT = os.getenv("PAYPAL_CLIENT_ID")
        PAYPAL_SECRET = os.getenv("PAYPAL_SECRET")
        PAYPAL_API = os.getenv("PAYPAL_API", "https://api-m.sandbox.paypal.com")
        if not (PAYPAL_CLIENT and PAYPAL_SECRET):
            return "pending"
        # Try to find order id token in link
        # Common param names: token, token=EC-..., or orderID in return url.
        token = None
        if "token=" in link:
            token = link.split("token=")[-1].split("&")[0]
        if not token and "ORDER-" in link:
            token = link.split("ORDER-")[-1].split("&")[0]
        if not token:
            return "pending"
        try:
            async with aiohttp.ClientSession() as session:
                auth = aiohttp.BasicAuth(PAYPAL_CLIENT, PAYPAL_SECRET)
                token_resp = await session.post(f"{PAYPAL_API}/v1/oauth2/token", data={"grant_type": "client_credentials"}, auth=auth, timeout=10)
                if token_resp.status in (200, 201):
                    token_data = await token_resp.json()
                    access_token = token_data.get("access_token")
                    headers = {"Authorization": f"Bearer {access_token}"}
                    order_resp = await session.get(f"{PAYPAL_API}/v2/checkout/orders/{token}", headers=headers, timeout=10)
                    if order_resp.status == 200:
                        order_json = await order_resp.json()
                        status = order_json.get("status", "").lower()
                        if status in ("completed", "captured", "paid"):
                            return "paid"
                        if status in ("created", "pending"):
                            return "pending"
        except Exception:
            return "pending"
        return "pending"

    # Qiwi: link may contain 'billId' or be on qiwi domain: try to extract bill id
    if "qiwi" in link or "payUrl" in link:
        QIWI_TOKEN = os.getenv("QIWI_API_KEY")
        QIWI_BASE = os.getenv("QIWI_API_BASE", "https://api.qiwi.com/partner/bill/v1")
        if not QIWI_TOKEN:
            return "pending"
        # attempt to parse billId param
        bill_id = None
        if "billId=" in link:
            bill_id = link.split("billId=")[-1].split("&")[0]
        if not bill_id and "/bills/" in link:
            bill_id = link.split("/bills/")[-1].split("?")[0]
        if not bill_id:
            return "pending"
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {QIWI_TOKEN}"}
                resp = await session.get(f"{QIWI_BASE}/bills/{bill_id}", headers=headers, timeout=10)
                if resp.status == 200:
                    data = await resp.json()
                    status = data.get("status", {}).get("value")
                    if status == "PAID":
                        return "paid"
                    if status in ("WAITING", "CREATED"):
                        return "pending"
        except Exception:
            return "pending"
        return "pending"

    # Unknown provider -> cannot verify automatically
    return "pending"


# ----- Callback: generate payment link and send to user -----
@router.callback_query(F.data.startswith("start_pay:"))
async def callback_start_pay(call: CallbackQuery):
    """
    When user clicks "To'lov qilamiz" (start_pay:<purchase_id>), generate a provider link
    and send it to the user. Save link into PendingPayment.receipt_file_id.
    """
    _, sid = call.data.split(":", 1)
    try:
        pid = int(sid)
    except Exception:
        await call.answer("Noto'g'ri so'rov.", show_alert=True)
        return

    payment = get_pending_payment(pid)
    if not payment:
        await call.answer("To'lov topilmadi.", show_alert=True)
        return

    payable = int(payment.get("payable", 0) or 0)
    label = payment.get("label") or human_name(payment.get("tariff", "tariff"), payment.get("plan", "plan")) or "To'lov"

    await call.answer()  # remove loading indicator

    try:
        link = await _generate_payment_link(payable, label, pid)
    except Exception:
        link = None

    if not link:
        await answer_with_sticker(call.message, "❌ Toʻlov havolasi yaratilishda xatolik yuz berdi. Iltimos, keyinroq urinib koʻring.", sticker_file_id=STICKER_TARIFF)
        return

    # Save link in DB (receipt_file_id)
    try:
        update_pending_payment(pid, {"receipt_file_id": str(link), "status": "awaiting_payment"})
    except Exception:
        # non-fatal
        pass

    text = (
        f"🧾 Toʻlov havolasi tayyor:\n\n{link}\n\n"
        f"💳 Toʻlov summasi: {payable:,} so'm\n\n"
        "Toʻlovni amalga oshirgach, «To‘lovni tekshirish» tugmasi orqali avtomatik tekshiruvni boshlang yoki «Men to‘lov qildim» tugmasi orqali xabar bering."
    )
    try:
        await answer_with_sticker(call.message, text, sticker_file_id=STICKER_TARIFF, reply_markup=pay_link_kb(pid))
    except Exception:
        try:
            await call.message.answer(text, reply_markup=pay_link_kb(pid))
        except Exception:
            pass


# ----- Callback: check payment status via provider -----
@router.callback_query(F.data.startswith("check_pay:"))
async def callback_check_pay(call: CallbackQuery):
    """
    When user clicks "To'lovni tekshirish" -> attempt verification via provider APIs.
    If paid -> mark DB approved and notify user.
    """
    _, sid = call.data.split(":", 1)
    try:
        pid = int(sid)
    except Exception:
        await call.answer("Noto'g'ri so'rov.", show_alert=True)
        return

    payment = get_pending_payment(pid)
    if not payment:
        await call.answer("To'lov topilmadi.", show_alert=True)
        return

    link = payment.get("receipt_file_id") or ""
    await call.answer("To'lov holati tekshirilmoqda… Iltimos kuting.", show_alert=False)

    try:
        status = await _verify_payment_by_link(link)
    except Exception:
        status = "pending"

    if status == "paid":
        # mark approved
        try:
            update_pending_payment(pid, {"status": "approved", "approved_at": time.time()})
        except Exception:
            pass
        # Notify user
        try:
            await answer_with_sticker(call.message, "✅ To‘lov muvaffaqiyatli amalga oshirildi!", sticker_file_id=STICKER_TARIFF)
        except Exception:
            try:
                await call.message.answer("✅ To‘lov muvaffaqiyatli amalga oshirildi!")
            except Exception:
                pass
        await call.answer()
        return

    if status == "pending":
        try:
            await answer_with_sticker(call.message, "⏳ To‘lov hali kelmagan. Iltimos, bir necha daqiqa kuting va qayta tekshiring.", sticker_file_id=STICKER_TARIFF)
        except Exception:
            try:
                await call.message.answer("⏳ To‘lov hali kelmagan. Iltimos, bir necha daqiqa kuting va qayta tekshiring.")
            except Exception:
                pass
        await call.answer()
        return

    # fallback: failed
    try:
        await answer_with_sticker(call.message, "❌ To‘lov amalga oshmadi yoki tekshirishda xatolik yuz berdi. Iltimos, adminga murojaat qiling.", sticker_file_id=STICKER_TARIFF)
    except Exception:
        try:
            await call.message.answer("❌ To‘lov amalga oshmadi yoki tekshirishda xatolik yuz berdi. Iltimos, adminga murojaat qiling.")
        except Exception:
            pass
    await call.answer()


# ----- Callback: manual confirm (paid_now:<pid>) -----
@router.callback_query(F.data.startswith("paid_now:"))
async def callback_paid_now_with_id(call: CallbackQuery):
    """
    Manual confirmation: mark purchase as approved.
    This is intended for admins or trusted manual flows.
    """
    _, sid = call.data.split(":", 1)
    try:
        pid = int(sid)
    except Exception:
        await call.answer("Noto'g'ri so'rov.", show_alert=True)
        return

    payment = get_pending_payment(pid)
    if not payment:
        await call.answer("To'lov topilmadi.", show_alert=True)
        return

    try:
        update_pending_payment(pid, {"status": "approved", "approved_at": time.time()})
    except Exception:
        pass

    try:
        await answer_with_sticker(call.message, "✅ To‘lov muvaffaqiyatli amalga oshirildi!", sticker_file_id=STICKER_TARIFF)
    except Exception:
        try:
            await call.message.answer("✅ To‘lov muvaffaqiyatli amalga oshirildi!")
        except Exception:
            pass
    await call.answer("Tasdiqlandi.")


# ----- Callback: start payment via Telegram invoice -----
@router.callback_query(F.data.startswith("start_pay:"))
async def start_pay_callback(call: CallbackQuery):
    """
    Callback triggered when user presses "To'lov qilamiz" (start_pay:{purchase_id}).
    We fetch the purchase record and send an invoice to the user via Telegram Payments.
    """
    await call.answer()  # remove loading indicator

    try:
        _, sid = call.data.split(":", 1)
        pid = int(sid)
    except Exception:
        await answer_with_sticker(call.message, "❌ Noto'g'ri so'rov.", sticker_file_id=STICKER_TARIFF)
        return

    payment = get_pending_payment(pid)
    if not payment:
        await answer_with_sticker(call.message, "❌ To'lov topilmadi yoki muddati o'tgan.", sticker_file_id=STICKER_TARIFF)
        return

    payable = int(payment.get("payable", 0) or 0)
    if payable <= 0:
        # Treat as free / fully covered by bonus; mark approved immediately
        try:
            update_pending_payment(pid, {"status": "approved", "approved_at": dt.datetime.utcnow()})
            user_db = get_user_by_tg(call.from_user.id)
            days = duration_days(payment.get("plan", "month") or "month")
            if user_db:
                activate_tariff(user_db.id, payment.get("tariff"), days)
            await answer_with_sticker(call.message, "✅ To‘lov muvaffaqiyatli amalga oshirildi!", sticker_file_id=STICKER_TARIFF)
        except Exception:
            await answer_with_sticker(call.message, "❌ To'lovni tasdiqlashda xatolik yuz berdi.", sticker_file_id=STICKER_TARIFF)
        return

    # Check provider token
    provider_token = STRIPE_PROVIDER_TOKEN
    if not provider_token:
        # No provider configured; send fallback link and instructions
        link = payment.get("receipt_file_id") or f"https://pay.example.com/pay?amount={payable}&pid={pid}"
        text = (
            f"🔗 To‘lov havolasi:\n{link}\n\n"
            "⚠ To‘lovni amalga oshirib, keyin «Men to‘lov qildim» tugmasini bosing."
        )
        await answer_with_sticker(call.message, text, sticker_file_id=STICKER_TARIFF, reply_markup=pay_link_kb(pid))
        return

    # Prepare invoice parameters
    title = payment.get("label") or "Obuna to‘lovi"
    description = f"{title} — {payable:,} {PAYMENT_CURRENCY}"
    payload = str(pid)  # we'll use purchase_id in payload
    currency = PAYMENT_CURRENCY or "UZS"

    # Build prices: Telegram expects amounts in the smallest units for some providers.
    # Aiogram's LabeledPrice requires amount as integer number of the smallest currency units.
    # Here we attempt to send as integer (no decimals) — adjust as per your provider/currency.
    try:
        # LabeledPrice(amount) expects integer (cents) according to aiogram; for safety pass as integer of currency * 100 if necessary.
        price_obj = [LabeledPrice(label=title, amount=int(payable))]
    except Exception:
        price_obj = [LabeledPrice(label=title, amount=int(payable))]

    try:
        # send_invoice is available on bot object
        await bot.send_invoice(
            chat_id=call.from_user.id,
            title=title,
            description=description,
            payload=payload,
            provider_token=provider_token,
            currency=currency,
            prices=price_obj,
            start_parameter=f"pay_{pid}",
            need_name=False,
            need_phone_number=False,
            need_email=False,
            need_shipping_address=False,
            is_flexible=False,
        )
    except Exception as e:
        # fallback: send link + instructions
        link = payment.get("receipt_file_id") or f"https://pay.example.com/pay?amount={payable}&pid={pid}"
        await answer_with_sticker(call.message, f"❌ To‘lovni boshlashda xatolik: {e}\n\nQuyidagi havola orqali to‘lovni bajaring:\n{link}", sticker_file_id=STICKER_TARIFF, reply_markup=pay_link_kb(pid))
        return

# Pre-checkout query handler (Telegram requires answering pre_checkout)
@router.pre_checkout_query()
async def handle_pre_checkout(pre_checkout: PreCheckoutQuery):
    """
    Accept pre-checkout queries. Telegram sends PreCheckoutQuery before finalizing payment.
    We must respond with answer_pre_checkout_query(OK=True) to allow payment.
    """
    try:
        await pre_checkout.answer(ok=True)
    except Exception:
        # Attempt to decline politely
        try:
            await pre_checkout.answer(ok=False, error_message="To'lovni qabul qila olmadik, keyinroq urinib ko'ring.")
        except Exception:
            pass

# Successful payment handler: Telegram sends a message with successful_payment
@router.message(F.successful_payment)
async def handle_successful_payment(message: Message):
    """
    Called when Telegram forwards the successful_payment message after payment completes.
    We extract the payload (purchase_id), update DB, activate tariff and notify user.
    """
    success = message.successful_payment
    if not success:
        return

    # payload is the purchase id we set in send_invoice
    payload = getattr(success, "invoice_payload", None) or getattr(success, "payload", None)
    try:
        pid = int(payload)
    except Exception:
        pid = None

    # collect provider info
    provider_payment_charge_id = getattr(success, "provider_payment_charge_id", None)
    telegram_payment_charge_id = getattr(success, "telegram_payment_charge_id", None)

    user_tg = message.from_user.id

    if pid:
        # Update pending payment record
        try:
            update_pending_payment(pid, {
                "status": "approved",
                "approved_at": dt.datetime.utcnow(),
                "receipt_file_id": provider_payment_charge_id or telegram_payment_charge_id
            })
        except Exception:
            # non-fatal
            pass

        # Activate tariff for the user
        try:
            pay = get_pending_payment(pid)
            if pay:
                tariff = pay.get("tariff")
                plan = pay.get("plan")
                days = duration_days(plan) or 30
                # Find DB user by telegram id
                user_db = get_user_by_tg(user_tg)
                if user_db:
                    activate_tariff(user_db.id, tariff, days)
        except Exception:
            pass

    # Notify user
    try:
        await answer_with_sticker(message, "✅ To‘lov muvaffaqiyatli amalga oshirildi! Tarifingiz faollashtirildi.", sticker_file_id=STICKER_TARIFF)
    except Exception:
        try:
            await message.answer("✅ To‘lov muvaffaqiyatli amalga oshirildi! Tarifingiz faollashtirildi.")
        except Exception:
            pass

# Optional: fallback callback "paid_now:{pid}" used when provider links were used
@router.callback_query(F.data.startswith("paid_now:"))
async def paid_now_callback(call: CallbackQuery):
    """
    Manual confirmation button when user uses external link and then presses "Men to'lov qildim".
    Admin still needs to verify via receipt/last4 flow, but we update pending status to awaiting_review.
    """
    await call.answer()
    try:
        _, sid = call.data.split(":", 1)
        pid = int(sid)
    except Exception:
        await answer_with_sticker(call.message, "❌ Noto'g'ri so'rov.", sticker_file_id=STICKER_TARIFF)
        return

    try:
        update_pending_payment(pid, {"status": "awaiting_review"})
    except Exception:
        pass

    await answer_with_sticker(call.message, "✅ To‘lov haqidagi ma'lumot qabul qilindi. Administratorlar tekshiradi. Iltimos biroz kuting.", sticker_file_id=STICKER_TARIFF)

# Expose router for register_all_handlers to include
# (register_all_handlers must include "handlers.payments")
