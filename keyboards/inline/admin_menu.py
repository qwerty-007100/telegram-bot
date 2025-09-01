from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def admin_menu_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="📢 Barchaga xabar yuborish", callback_data="broadcast_all")
    kb.button(text="📊 Hisobot olish", callback_data="report_menu")
    kb.adjust(1)  # Har qatorda 1 ta tugma
    return kb.as_markup()
