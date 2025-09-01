from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from datetime import datetime, timedelta
import logging

from loader import bot, answer_with_sticker
from config import ADMIN_ID, DOCTOR_ID, STICKER_TARIFF
from database import get_report_data, get_all_users, deactivate_expired_tariffs, get_top_referrer

logger = logging.getLogger(__name__)
router = Router()


class BroadcastStates(StatesGroup):
    text = State()


class StaffReplyStates(StatesGroup):
    waiting_reply = State()


# Reply-keyboard helpers
def admin_main_keyboard():
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📢 Barchaga xabar yuborish")],
            [KeyboardButton(text="📊 Hisobot olish")],
            # removed 'Admin paneldan chiqish' per UX request
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )
    return kb


def report_options_keyboard():
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="1 kunlik hisobot")],
            [KeyboardButton(text="1 haftalik hisobot")],
            [KeyboardButton(text="1 oylik hisobot")],
            [KeyboardButton(text="Admin paneldan chiqish")],

        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )
    return kb


# Admin entry
@router.message(lambda m: m.text == '/admin')
async def admin_entry(message: Message, state: FSMContext | None = None):
    caller = message.from_user.id
    logger.info("admin_panel called by %s (ADMIN_ID=%s)", caller, ADMIN_ID)
    if caller not in (ADMIN_ID, DOCTOR_ID):
        return await answer_with_sticker(message, "⛔ Siz admin emassiz!", sticker_file_id=STICKER_TARIFF)

    try:
        if state is not None:
            await state.clear()
    except Exception:
        pass

    await answer_with_sticker(
        message,
        "👋 Admin panelga xush kelibsiz!",
        sticker_file_id=STICKER_TARIFF,
        reply_markup=admin_main_keyboard()
    )


# Broadcast flow
@router.message(lambda m: m.text == '📢 Barchaga xabar yuborish')
async def admin_broadcast_start(message: Message, state: FSMContext):
    caller = message.from_user.id
    if caller not in (ADMIN_ID, DOCTOR_ID):
        return await message.answer("⛔ Siz bu amalni bajarishga ruxsatga ega emassiz.")
    await answer_with_sticker(message, "✏️ Iltimos, barcha foydalanuvchilarga yuboriladigan matnni kiriting:", sticker_file_id=STICKER_TARIFF)
    await state.set_state(BroadcastStates.text)


@router.message(BroadcastStates.text)
async def admin_broadcast_process(message: Message, state: FSMContext):
    text = message.text or ""
    signature = "Bakumov Qiziriq Klinikasi"
    full_text = f"{signature}:\n\n{text}"

    try:
        users = get_all_users()
    except Exception as e:
        logger.exception("Failed to get users for broadcast: %s", e)
        await message.answer("Xatolik: foydalanuvchilar ro'yxatini olishda xatolik yuz berdi.")
        await state.clear()
        return

    sent = 0
    for u in users:
        try:
            user_id = getattr(u, 'telegram_id', None)
            if not user_id:
                continue
            await bot.send_message(user_id, full_text)
            sent += 1
        except Exception as e:
            logger.exception("Broadcast send failed for %s: %s", user_id, e)
            continue

    if sent == 0:
        # send test copy to admin so they see the broadcast content
        try:
            await bot.send_message(ADMIN_ID, f"[TEST BROADCAST]\n{full_text}")
        except Exception:
            pass

    await answer_with_sticker(message, f"✅ {sent} ta foydalanuvchiga xabar yuborildi.", sticker_file_id=STICKER_TARIFF)
    await state.clear()
    await answer_with_sticker(message, "Admin panelga qaytildi.", sticker_file_id=STICKER_TARIFF, reply_markup=admin_main_keyboard())


# Reports
async def _send_report_for_range(message: Message, start: datetime, end: datetime, title: str):
    try:
        report = get_report_data(start, end)
    except Exception as e:
        logger.exception("get_report_data failed: %s", e)
        await message.answer("Hisobot olinayotganda xatolik yuz berdi.")
        return

    new_users = report.get('new_users', 0)
    total_sum = report.get('total_sum', 0)
    tariff_sales = report.get('tariff_sales', {})
    total_users = report.get('total_users', None)
    purchased = report.get('purchased', None)
    not_purchased = report.get('not_purchased', None)

    text = f"📊 {title}\n"
    text += f"📅 {start.strftime('%d.%m.%Y')} - {end.strftime('%d.%m.%Y')}\n"
    text += f"👥 Yangi foydalanuvchilar: {new_users}\n"
    if total_users is not None:
        text += f"👥 Jami foydalanuvchilar: {total_users}\n"
    if purchased is not None and not_purchased is not None:
        text += f"🛒 Tarif sotib olganlar: {purchased}\n"
        text += f"🚫 Tarif sotib olmaganlar: {not_purchased}\n"
    text += f"💰 Umumiy daromad: {total_sum:,} UZS\n\n"
    text += "📦 Tarif sotuvlari:\n"
    if isinstance(tariff_sales, dict) and tariff_sales:
        for tariff, plans in tariff_sales.items():
            text += f"  - {tariff}:\n"
            if isinstance(plans, dict):
                for plan, cnt in plans.items():
                    text += f"      • {plan}: {cnt}\n"
            else:
                text += f"      • {plans}\n"
    else:
        text += "  - Ma'lumot mavjud emas\n"

    kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Admin panelga qaytish')]], resize_keyboard=True)
    await message.answer(text, reply_markup=kb)


@router.message(lambda m: m.text == '📊 Hisobot olish')
async def admin_reports_menu(message: Message):
    caller = message.from_user.id
    if caller not in (ADMIN_ID, DOCTOR_ID):
        return await message.answer("⛔ Siz bu amalni bajarishga ruxsatga ega emassiz.")
    await answer_with_sticker(message, "📊 Hisobot turini tanlang:", sticker_file_id=STICKER_TARIFF, reply_markup=report_options_keyboard())


@router.message(lambda m: m.text == '1 kunlik hisobot')
async def report_1day(message: Message):
    now = datetime.now()
    start = datetime(now.year, now.month, now.day)
    await _send_report_for_range(message, start, now, '1 kunlik hisobot')


@router.message(lambda m: m.text == '1 haftalik hisobot')
async def report_7day(message: Message):
    now = datetime.now()
    start = now - timedelta(days=7)
    await _send_report_for_range(message, start, now, '7 kunlik hisobot')


@router.message(lambda m: m.text == '1 oylik hisobot')
async def report_30day(message: Message):
    now = datetime.now()
    start = now - timedelta(days=30)
    await _send_report_for_range(message, start, now, '30 kunlik hisobot')


# Catch various 'admin panel' return/exit button texts (case-insensitive, substring match)
@router.message(lambda m: m.text and 'admin panel' in m.text.lower())
async def admin_panel_return(message: Message, state: FSMContext | None = None):
    caller = message.from_user.id
    if caller not in (ADMIN_ID, DOCTOR_ID):
        return await message.answer("⛔ Siz bu amalni bajarishga ruxsatga ega emassiz.")
    try:
        if state is not None:
            await state.clear()
    except Exception:
        pass
    await answer_with_sticker(message, '👋 Admin panelga qaytildi.', sticker_file_id=STICKER_TARIFF, reply_markup=admin_main_keyboard())


# 'Admin panelga qaytish' handler removed — navigation is handled via the main keyboard/actions.


# Staff reply via command: /reply <tg_id> <text>
@router.message(lambda m: m.text and m.text.startswith('/reply'))
async def admin_reply_command(message: Message):
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        return await message.answer("Iltimos, format: /reply <user_tg> <xabar>")
    try:
        user_tg = int(parts[1])
    except Exception:
        return await message.answer("Iltimos, to'g'ri telegram id kiriting.")
    reply_text = parts[2]
    try:
        await bot.send_message(user_tg, reply_text)
        await message.answer('✅ Xabar yuborildi.')
    except Exception as e:
        logger.exception('Failed to send admin reply: %s', e)
        await message.answer(f"Xatolik: {e}")


# Inline button from ask_question: reply_q_<telegram_id>
@router.callback_query(lambda c: c.data and c.data.startswith('reply_q_'))
async def handle_reply_q(call: CallbackQuery, state: FSMContext):
    # acknowledge callback quickly to stop spinner
    try:
        await call.answer()
    except Exception:
        pass

    caller = call.from_user.id
    if caller not in (ADMIN_ID, DOCTOR_ID):
        await call.message.answer("⛔ Siz bu amalni bajarishga ruxsatga ega emassiz.")
        return

    data = call.data or ''
    # callback can be 'reply_q_<tg>' or 'reply_q_<tg>_<qid>'
    try:
        tail = data.split('reply_q_')[-1]
        parts = tail.split('_')
        target_tg = int(parts[0])
        question_id = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
    except Exception:
        await call.message.answer('Xatolik: maqsadli foydalanuvchi aniqlanmadi.')
        return

    # store target in FSM data and wait for admin message
    await state.set_state(StaffReplyStates.waiting_reply)
    await state.update_data(reply_target=target_tg, question_id=question_id)
    prompt = f"✉️ Foydalanuvchiga javob yuboring (tg id: {target_tg})"
    if question_id:
        prompt += f" — savol ID: {question_id}"
    prompt += "."
    await call.message.answer(prompt)



@router.callback_query(F.data == "report_menu")
async def report_menu_callback(call: CallbackQuery):
    """Show report options when admin clicks inline 'Hisobot olish' button."""
    caller = call.from_user.id
    if caller not in (ADMIN_ID, DOCTOR_ID):
        return await call.answer("⛔ Siz bu amalni bajarishga ruxsatga ega emassiz.", show_alert=True)

    # acknowledge the callback to remove the spinner
    try:
        await call.answer()
    except Exception:
        pass

    # send the same reply keyboard used in admin_reports_menu
    try:
        await answer_with_sticker(call.message, "📊 Hisobot turini tanlang:", sticker_file_id=STICKER_TARIFF, reply_markup=report_options_keyboard())
    except Exception:
        try:
            await call.message.answer("📊 Hisobot turini tanlang:", reply_markup=report_options_keyboard())
        except Exception:
            pass


@router.message(StaffReplyStates.waiting_reply)
async def staff_send_reply(message: Message, state: FSMContext):
    data = await state.get_data()
    target = data.get('reply_target')
    text = message.text or ''
    if not target:
        await message.answer('Xatolik: maqsadli foydalanuvchi topilmadi.')
        await state.clear()
        return
    sent_ok = False
    # Friendly signature to prepend so users see it's from the doctor/staff
    signature = "Doctor Mirsaid javobi — "
    try:
        # Prefer to forward the original message for non-text content so attachments/captions are preserved
        if text:
            payload = f"{signature}{text}"
            await bot.send_message(target, payload)
            sent_ok = True
        elif getattr(message, 'photo', None):
            # send largest photo available with caption prefixed
            file_id = message.photo[-1].file_id
            caption = message.caption or ""
            prefixed = f"{signature}{caption}" if caption else signature.rstrip(' — ')
            await bot.send_photo(target, file_id, caption=(prefixed if prefixed else None))
            sent_ok = True
        elif getattr(message, 'document', None):
            caption = message.caption or ""
            prefixed = f"{signature}{caption}" if caption else signature.rstrip(' — ')
            await bot.send_document(target, message.document.file_id, caption=(prefixed if prefixed else None))
            sent_ok = True
        elif getattr(message, 'sticker', None):
            # stickers don't have caption support
            await bot.send_message(target, signature + "sticker")
            await bot.send_sticker(target, message.sticker.file_id)
            sent_ok = True
        else:
            # fallback: forward the original message to preserve content
            try:
                # send a small prefixed note then forward
                await bot.send_message(target, signature)
                await bot.forward_message(target, message.chat.id, message.message_id)
                sent_ok = True
            except Exception:
                # final fallback: try to send text if present, else notify admin of failure
                if text:
                    await bot.send_message(target, signature + text)
                    sent_ok = True

        if sent_ok:
            await message.answer('✅ Javob yuborildi.')
            # send a friendly follow-up to the user asking if they have more questions
            try:
                follow = (
                    "Sizning savolingizga javob keldi.👆🏻\n\n"
                    "Yana boshqa savollaringiz bormi? Agar bo'lsa, savollaringizni 'Savol yozish' tugmasi orqali yozishingiz mumkin."
                )
                await bot.send_message(target, follow)
            except Exception:
                # non-fatal if follow-up fails
                pass
        else:
            await message.answer('❌ Xatolik: xabar yuborilmadi. Iltimos qayta urinib ko\'ring.')
    except Exception as e:
        logger.exception('Failed to send staff reply to %s: %s', target, e)
        try:
            await message.answer(f'Xatolik yuborishda: {e}')
        except Exception:
            pass

    await state.clear()


# Scheduler helpers
async def send_10_day_report():
    now = datetime.utcnow()
    start = now - timedelta(days=10)
    report = get_report_data(start, now)
    text = (
        f"📊 10 kunlik hisobot\n"
        f"📅 {start.strftime('%d.%m.%Y')} - {now.strftime('%d.%m.%Y')}\n"
        f"👥 Yangi foydalanuvchilar: {report.get('new_users', 0)}\n"
        f"💰 Umumiy daromad: {report.get('total_sum', 0):,} UZS\n"
        f"Jami foydalanuvchilar: {report.get('total_users', 0)}\n"
    )
    await bot.send_message(ADMIN_ID, text)


async def send_monthly_report():
    now = datetime.utcnow()
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    report = get_report_data(start, now)
    text = (
        f"📊 Oylik hisobot\n"
        f"📅 {start.strftime('%d.%m.%Y')} - {now.strftime('%d.%m.%Y')}\n"
        f"👥 Yangi foydalanuvchilar: {report.get('new_users', 0)}\n"
        f"💰 Umumiy daromad: {report.get('total_sum', 0):,} UZS\n"
        f"Jami foydalanuvchilar: {report.get('total_users', 0)}\n"
    )
    top = None
    try:
        top = get_top_referrer()
    except Exception:
        pass
    if top:
        text += f"\n🏆 Eng yaxshi referal: {top.get('name')} ({top.get('phone')}) - {top.get('count')} foydalanuvchi"
    await bot.send_message(ADMIN_ID, text)


async def manage_expired_subscriptions():
    try:
        expired = deactivate_expired_tariffs()
        for u in expired:
            try:
                tgid = getattr(u, 'telegram_id', None)
                if not tgid:
                    continue
                await bot.send_message(tgid, "❗ Sizning tarifingiz muddati tugadi. Yangi tarif sotib olish uchun botdan foydalaning.")
            except Exception:
                pass
    except Exception as e:
        logger.exception("manage_expired_subscriptions failed: %s", e)
