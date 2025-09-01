import os
from dotenv import load_dotenv

# Load .env file if present (no error if missing)
load_dotenv()

# BOT_TOKEN: Telegram bot token. Set in environment or in a .env file:
# BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
BOT_TOKEN = os.getenv("BOT_TOKEN", "REPLACE_WITH_YOUR_BOT_TOKEN")

# ADMIN_ID and DOCTOR_ID: Telegram numeric user IDs for admin and doctor.
# Use 0 as default (no admin configured). Convert to int safely.
try:
    ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
except ValueError:
    ADMIN_ID = 0

try:
    DOCTOR_ID = int(os.getenv("DOCTOR_ID", "0"))
except ValueError:
    DOCTOR_ID = 0

# Payment / card settings (optional; used for manual bank card instructions)
PAYMENT_CARD = os.getenv("PAYMENT_CARD", "9860 0101 0114 6065")
PAYMENT_CARD_HOLDER = os.getenv("PAYMENT_CARD_HOLDER", "Botirov B.")

# Telegram Payments provider token (e.g. Stripe provider token for Telegram Payments)
# Set STRIPE_PROVIDER_TOKEN in your environment if you use Telegram's Payments API with Stripe.
STRIPE_PROVIDER_TOKEN = os.getenv("STRIPE_PROVIDER_TOKEN", None)

# Payment currency (3-letter ISO). Default to UZS (Uzbek som).
PAYMENT_CURRENCY = os.getenv("PAYMENT_CURRENCY", "UZS")

# Sticker file_ids (optional). Set these to sticker file_ids if you want stickers sent.
# Example in .env: STICKER_WELCOME=CAACAgIAAxkBAAEB...
STICKER_WELCOME = os.getenv("STICKER_WELCOME", None)
STICKER_TARIFF = os.getenv("STICKER_TARIFF", None)
STICKER_SOCIALS = os.getenv("STICKER_SOCIALS", None)

# Misc: retry/timeouts or other configurable values (optional)
HTTP_TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "15"))

# Expose __all__ for clarity
__all__ = [
    "BOT_TOKEN", "ADMIN_ID", "DOCTOR_ID",
    "PAYMENT_CARD", "PAYMENT_CARD_HOLDER",
    "STRIPE_PROVIDER_TOKEN", "PAYMENT_CURRENCY",
    "STICKER_WELCOME", "STICKER_TARIFF", "STICKER_SOCIALS",
    "HTTP_TIMEOUT"
]
