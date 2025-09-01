# file: handlers/main_menu.py
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from loader import answer_with_sticker
from keyboards import get_menu_for
from config import STICKER_WELCOME

router = Router()

@router.message(F.text == "ℹ️ Bot haqida ma'lumot")
async def bot_info(message: Message):
    text = (
        "ℹ️ Bot haqida:\n\n"
        "Ushbu bot reproduktiv salomatlik bo'yicha umumiy ma'lumot va Doctor Mirsaid bilan "
        "onlayn maslahat olish imkonini beradi. Bot orqali tariflar, savol-javob va klinika xizmatlari haqida ma'lumot olishingiz mumkin."
    )
    await answer_with_sticker(message, text, sticker_file_id=STICKER_WELCOME, reply_markup=get_menu_for(message.from_user.id))

@router.message(F.text == "👨‍⚕️ Doctor Mirsaid haqida")
async def doctor_info(message: Message):
    text = (
        "👨‍⚕️ Doctor Mirsaid haqida:\n\n"
        "Doctor Mirsaid — reproduktiv salomatlik bo'yicha tajribali mutaxassis. "
        "Ko'p yillik amaliyot va ko'plab muvaffaqiyatli holatlar mavjud. Telefon va konsultatsiya tartibi bot orqali ko'rsatiladi."
    )
    await answer_with_sticker(message, text, sticker_file_id=STICKER_WELCOME, reply_markup=get_menu_for(message.from_user.id))

@router.message(F.text == "📌 Tariflar haqida")
async def tariffs_info(message: Message):
    # Full tariff descriptions (as requested)
    text = (
        "💳 Tariflar haqida ma'lumot\n\n"
        "📌 Free:\n"
        "- Kunlik: 2 ta bepul savol\n"
        "- Javob: 12-24 soat ichida\n\n"
        "📌 Pro:\n"
        "- Kunlik: 19 ta savol\n"
        "- Javob: 2-4 soat ichida\n\n"
        "📌 Premium:\n"
        "- Kunlik: 49 ta savol\n"
        "- Javob: 1-2 soat ichida\n\n"
        "📌 Homiladorlik:\n"
        "- 1 oy: 599 savol (Homiladorlik 1 oy)\n"
        "- 9 oy: 5999 savol (Homiladorlik 9 oy)\n"
        "- Homiladorlik maktabi ilovasi 1 oy premium bepul\n\n"
        "📌 Farzand rejalash:\n"
        "- Kunlik: 149 ta savol\n"
        "- Er-xotin uchun barcha xizmatlarda 20% chegirma\n\n"
        "Agar sotib olmoqchi bo'lsangiz, pastdagi tugmadan foydalaning."
    )

    # contextual keyboard with direct "Tarif sotib olish" button and "Orqaga"
    tariffs_kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏷 Tarif sotib olish")],
            [KeyboardButton(text="Orqaga")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await answer_with_sticker(message, text, sticker_file_id=STICKER_WELCOME, reply_markup=tariffs_kb)

@router.message(F.text == "🏷 Tarif sotib olish")
async def buy_tariff_entry(message: Message):
    # This handler purposely delegates to purchase flow which listens to the exact text "Tarif sotib olish".
    # The purchase handler will start the FSM. Here we simply redirect user to press the same button,
    # but because this router is included together with handlers/purchase.py, the purchase.start_purchase
    # (which also handles F.text == "Tarif sotib olish") will be triggered. To be safe, send a short hint.
    await answer_with_sticker(message, "Sizni sotib olish sahifasiga yo'naltiryapmiz… Iltimos, kerakli tarifni tanlang.", sticker_file_id=STICKER_WELCOME, reply_markup=get_menu_for(message.from_user.id))

@router.message(F.text == "🧾 Mening tarifim")
async def my_tariff(message: Message):
    await answer_with_sticker(message, "📄 Sizning joriy tarifingiz: bu yerda joriy tarif va qolgan savollar ko'rsatiladi. (Agar ro'yxatdan o'tmagan bo'lsangiz, /start bilan ro'yxatdan o'ting.)", sticker_file_id=STICKER_WELCOME, reply_markup=get_menu_for(message.from_user.id))

@router.message(F.text == "➕ Botga odam qo‘shish")
async def add_user(message: Message):
    # Provide referral link
    me = await message.bot.get_me()
    username = getattr(me, "username", None)
    user_id = message.from_user.id
    if username:
        ref_link = f"https://t.me/{username}?start={user_id}"
    else:
        ref_link = f"https://t.me/{user_id}"
    await answer_with_sticker(message, f"📢 Sizning referal havolangiz:\n{ref_link}\nHar bir ro'yxatdan o'tgan do'stingiz uchun 1000 so'm bonus olasiz.", sticker_file_id=STICKER_WELCOME, reply_markup=get_menu_for(message.from_user.id))

@router.message(F.text == "🌐 Mirsaid BAKUMOVning ijtimoiy tarmoqlari")
async def socials(message: Message):
    await answer_with_sticker(message, "🌐 Ijtimoiy tarmoqlar:\nTelegram kanal: https://t.me/MirsaidKanal\nTelegram guruh: https://t.me/MirsaidGuruh\nInstagram: https://instagram.com/mirsaid_bakumov\nYouTube: https://youtube.com/@mirsaidbakumov", sticker_file_id=STICKER_WELCOME, reply_markup=get_menu_for(message.from_user.id))

# 'Foydali ma'lumotlar' menu removed per request

@router.message(lambda m: m.text in ["📞 Admin bilan bog‘lanish", "Admin bilan bog'lanish", "Admin bilan bog‘lanish"])
async def contact_admin(message: Message):
    # Delegate to the central admin_contact handler to keep behavior consistent
    from handlers import admin_contact as admin_mod
    await admin_mod.admin_contact(message)

@router.message(F.text == "📑 Savol yozish")
async def ask_question(message: Message):
    await answer_with_sticker(message, "✍️ Savol yozish: Iltimos, savolingizni yozib yuboring. Doctor Mirsaid yoki admin tez orada javob beradi.", sticker_file_id=STICKER_WELCOME, reply_markup=get_menu_for(message.from_user.id))

@router.message(F.text == "📜 Maxfiylik siyosati")
async def privacy_policy(message: Message):
    await answer_with_sticker(message, "📜 Maxfiylik siyosati: Foydalanuvchi ma'lumotlari faqat xizmat ko'rsatish uchun saqlanadi va uchinchi tomonlarga berilmaydi.", sticker_file_id=STICKER_WELCOME, reply_markup=get_menu_for(message.from_user.id), parse_mode="Markdown")

@router.message(F.text == "⚠️ Tibbiy maslahatlar ogohlantirishi")
async def medical_warning(message: Message):
    await answer_with_sticker(message, "⚠️ Tibbiy maslahatlar ogohlantirishi: Bot tomonidan berilgan ma'lumotlar umumiy maslahat sifatida taqdim etiladi; aniq tashxis va davolash uchun shifokorga murojaat qiling.", sticker_file_id=STICKER_WELCOME, reply_markup=get_menu_for(message.from_user.id), parse_mode="Markdown")
# (Clean end of file - duplicate/garbled blocks removed)
