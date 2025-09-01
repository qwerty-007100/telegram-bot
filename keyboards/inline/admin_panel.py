from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def admin_panel_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="📢 Barchaga xabar yuborish", callback_data="broadcast_all")
    kb.adjust(1)  # Har qatorda 1 ta tugma
    return kb.as_markup()
