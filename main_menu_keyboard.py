from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def main_menu_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(text="Option 1", callback_data="opt_1"),
        InlineKeyboardButton(text="Option 2", callback_data="opt_2"),
    )
    return keyboard