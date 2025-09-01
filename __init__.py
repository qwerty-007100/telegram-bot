from .register_all_handlers import register_all_handlers

# Import all router modules here
from . import start, purchase, tariffs, my_tariff, socials, useful_info, reply, ask_question, referal, register, payments, default, doctor_info, info_bot, admin_contact

# Create a list of all routers
routers = [
    start.router,
    purchase.router,
    tariffs.router,
    my_tariff.router,
    socials.router,
    useful_info.router,
    reply.router,
    ask_question.router,
    referal.router,
    register.router,
    payments.router,
    default.router,
    doctor_info.router,
    info_bot.router,
    admin_contact.router
]

__all__ = ["register_all_handlers", "routers"]