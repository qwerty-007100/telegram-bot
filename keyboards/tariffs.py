from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Asosiy tariflar menyusi
tariff_main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Pro"), KeyboardButton(text="Premium")],
        [KeyboardButton(text="Homiladorlik"), KeyboardButton(text="Farzand ko‘rishni rejalashtirish")],
        [KeyboardButton(text="Bosh menuga qaytish")]
    ],
    resize_keyboard=True
)

# Pro / Premium / Farzand rejalash uchun ichki menyu
weekly_monthly_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="1 haftalik"), KeyboardButton(text="1 oylik")],
        [KeyboardButton(text="Orqaga")]
    ],
    resize_keyboard=True
)

# Homiladorlik uchun ichki menyu
homiladorlik_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Homiladorlik 1 oy"), KeyboardButton(text="Homiladorlik 9 oy")],
        [KeyboardButton(text="Orqaga")]
    ],
    resize_keyboard=True
)

