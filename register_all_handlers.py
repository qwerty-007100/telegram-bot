import importlib
import logging
from aiogram import Dispatcher

# Ensure basic logging is configured so startup issues are visible on console
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODULES = [
    "handlers.start",
    "handlers.register",
    "handlers.default",
    "handlers.info_bot",
    "handlers.doctor_info",
    "handlers.referal",
    "handlers.socials",
    # useful_info removed per request (not needed)
    "handlers.tariffs",
    "handlers.purchase",
    "handlers.payments",
    "handlers.ask_question",
    "handlers.my_tariff",
    "handlers.reply",
    "handlers.main_menu",            # <-- added to ensure main menu handlers are registered
    "handlers.admin_contact",
    "handlers.admin.broadcast",
    "handlers.admin.panel",
    # temporary debug-only module to confirm callback delivery
    "handlers.admin.debug_callbacks",
]

def register_all_handlers(dp: Dispatcher):
    for name in MODULES:
        try:
            mod = importlib.import_module(name)
            router = getattr(mod, "router", None)
            if router:
                dp.include_router(router)
                logger.info("Included router: %s", name)
                # visible feedback for environments without logging config
                print(f"Included router: {name}")
            else:
                logger.warning("Module %s has no router", name)
                print(f"WARNING: Module {name} has no router")
        except Exception:
            logger.exception("Failed to import %s", name)
            print(f"Failed to import {name}; see logs for details")

__all__ = ["register_all_handlers"]