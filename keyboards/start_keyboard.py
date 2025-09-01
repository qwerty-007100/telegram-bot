from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

start_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Ro'yxatdan o'tish")]],
    resize_keyboard=True,
    one_time_keyboard=True
)

__all__ = ["start_keyboard"]