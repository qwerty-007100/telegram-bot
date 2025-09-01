from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Tekinga berilmaydigan variant
useful_info_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="1 haftalik obuna"), KeyboardButton(text="1 oylik obuna")],
        [KeyboardButton(text="Orqaga")]
    ],
    resize_keyboard=True
)

# Tekin beriladigan variant
useful_info_keyboard_with_free = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="1 haftalik obuna"), KeyboardButton(text="1 oylik obuna")],
        [KeyboardButton(text="1 haftalik obunani tekin olish")],
        [KeyboardButton(text="Orqaga")]
    ],
    resize_keyboard=True
)
