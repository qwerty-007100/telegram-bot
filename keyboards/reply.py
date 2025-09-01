from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

start_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Ro'yxatdan o'tish")]],
    resize_keyboard=True,
    one_time_keyboard=True
)

main_menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Bot haqida ma'lumot")],
        [KeyboardButton(text="Doctor MIRSAID haqida")],
    [KeyboardButton(text="Tariflar haqida")],
    [KeyboardButton(text="Savol yozish")]
    ],
    resize_keyboard=True
)
