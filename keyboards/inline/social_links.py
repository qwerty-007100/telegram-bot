from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def social_links_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="📢 Telegram kanal", url="https://t.me/MirsaidKanal")
    kb.button(text="👥 Telegram guruh", url="https://t.me/MirsaidGuruh")
    kb.button(text="📷 Instagram", url="https://instagram.com/mirsaid_bakumov")
    kb.button(text="▶️ YouTube", url="https://youtube.com/@mirsaidbakumov")
    kb.button(text="✅ Tekshirish", callback_data="check_socials")
    kb.adjust(1)  # Har qatorda 1 ta tugma
    return kb.as_markup()
