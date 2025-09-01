from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Canonical main menu used by handlers (texts must match handlers' checks)
main_menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="ℹ️ Bot haqida ma'lumot"), KeyboardButton(text="👨‍⚕️ Doctor Mirsaid haqida")],
    [KeyboardButton(text="📌 Tariflar haqida")],
    [KeyboardButton(text="➕ Botga odam qo‘shish")],
    [KeyboardButton(text="🌐 Mirsaid BAKUMOVning ijtimoiy tarmoqlari")],
        [KeyboardButton(text="📞 Admin bilan bog‘lanish"), KeyboardButton(text="📑 Savol yozish")],
        [KeyboardButton(text="📜 Maxfiylik siyosati"), KeyboardButton(text="⚠️ Tibbiy maslahatlar ogohlantirishi")]
    ],
    resize_keyboard=True
)

# Start keyboard used during registration start flow
start_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Ro'yxatdan o'tish")]],
    resize_keyboard=True,
    one_time_keyboard=True
)


# Keyboards for staff (admin / doctor) actions
admin_keyboard = ReplyKeyboardMarkup(
    keyboard=[
    [KeyboardButton(text="📊 Hisobot olish"), KeyboardButton(text="📢 Barchaga xabar yuborish")],
    # keep legacy text variant in case some handlers check without emoji
    [KeyboardButton(text="Hisobot olish")],
    ],
    resize_keyboard=True
)

doctor_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Orqaga")],
    ],
    resize_keyboard=True
)
