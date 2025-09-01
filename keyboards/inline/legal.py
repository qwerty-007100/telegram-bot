from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def legal_accept_kb() -> InlineKeyboardMarkup:
    """Inline keyboard for accepting legal terms."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Men qabul qilaman", callback_data="accept_legal")]
        ]
    )

def legal_menu_kb() -> InlineKeyboardMarkup:
    """Inline keyboard for navigating legal sections."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📜 Maxfiylik siyosati", callback_data="privacy_policy")],
            [InlineKeyboardButton(text="⚠️ Tibbiy maslahatlar ogohlantirishi", callback_data="medical_disclaimer")],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_main")]
        ]
    )
