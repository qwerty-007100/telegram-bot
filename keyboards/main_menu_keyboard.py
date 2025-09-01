from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="ℹ️ Bot haqida ma'lumot"), KeyboardButton(text="👨‍⚕️ Doctor MIRSAID haqida")],
    [KeyboardButton(text="📌 Tariflar haqida")],
    [KeyboardButton(text="📑 Savol yozish")]
    ],
    resize_keyboard=True
)

start_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Ro'yxatdan o'tish")]],
    resize_keyboard=True,
    one_time_keyboard=True
)