from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Bot haqida ma'lumot"), KeyboardButton(text="Doctor Mirsaid haqida")],
    [KeyboardButton(text="Tariflar haqida")],
    [KeyboardButton(text="Botga odam qo‘shish")],
    [KeyboardButton(text="Mirsaid BAKUMOVning ijtimoiy tarmoqlari")],
        [KeyboardButton(text="Admin bilan bog‘lanish"), KeyboardButton(text="Savol yozish")]
    ],
    resize_keyboard=True
)


# Staff keyboards
admin_keyboard = ReplyKeyboardMarkup(
    keyboard=[
    [KeyboardButton(text="📊 Hisobot olish"), KeyboardButton(text="📢 Barchaga xabar yuborish")],
    [KeyboardButton(text="Hisobot olish")],
        [KeyboardButton(text="Orqaga")],
    ],
    resize_keyboard=True
)

doctor_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Orqaga")],
    ],
    resize_keyboard=True
)
