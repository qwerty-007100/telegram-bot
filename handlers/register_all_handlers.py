import importlib
import logging
from aiogram import Dispatcher

logger = logging.getLogger(__name__)

# List of handler modules to load (adjust if you add/remove modules)
MODULES = [
    "handlers.start",
    "handlers.purchase",
    "handlers.tariffs",
    "handlers.my_tariff",
    "handlers.socials",
    "handlers.useful_info",
    "handlers.reply",
    "handlers.ask_question",
    "handlers.referal",
    "handlers.register",
    "handlers.payments",
    "handlers.default",
    "handlers.doctor_info",
    "handlers.info_bot",
    "handlers.admin_contact",
    "handlers.admin.broadcast",
]


def register_all_handlers(dp: Dispatcher):
    """
    Import modules listed in MODULES and include their `router` into the Dispatcher.
    Failures are logged and skipped.
    """
    for mod_name in MODULES:
        try:
            mod = importlib.import_module(mod_name)
            router = getattr(mod, "router", None)
            if router is not None:
                dp.include_router(router)
                logger.info("Included router from %s", mod_name)
            else:
                logger.warning(
                    "Module %s imported but no `router` attribute found.", mod_name
                )
        except Exception as e:
            logger.exception("Failed to import handlers module %s: %s", mod_name, e)


__all__ = ["register_all_handlers"]
