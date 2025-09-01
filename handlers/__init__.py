"""
handlers package initializer

Safely import top-level handler modules into package namespace so that
`from handlers import start, referal` works. Do not fail hard if some
modules can't be imported during startup (they'll be logged but the bot can still start).

Also expose register_all_handlers helper.
"""
from importlib import import_module
from typing import List

# List top-level handler module names that live under handlers/*.py
_TOP_MODULES: List[str] = [
    "start",
    "referal",
    "ask_question",
    "purchase",
    "tariffs",
    "my_tariff",
    "socials",
    "useful_info",
    "reply",
    "default",
    "doctor_info",
    "info_bot",
    "admin_contact",
    "register",
    "payments",
    "buy_payment",
    # add more top-level handler module names here if present
]

# Import modules into package namespace if available (best-effort)
for _name in _TOP_MODULES:
    try:
        _mod = import_module(f"handlers.{_name}")
        globals()[_name] = _mod
    except Exception:
        # Import errors are intentionally swallowed here to avoid hard startup failures.
        # Modules will still be attempted to be registered by register_all_handlers which logs issues.
        pass

# Import admin subpackage modules into package namespace under a distinct name if desired
try:
    _admin_broadcast = import_module("handlers.admin.broadcast")
    globals()["admin_broadcast"] = _admin_broadcast
except Exception:
    pass

# Expose register_all_handlers from handlers.register_all_handlers
try:
    from .register_all_handlers import register_all_handlers  # type: ignore
    __all__ = ["register_all_handlers"] + _TOP_MODULES + ["admin_broadcast"]
except Exception:
    # If register_all_handlers cannot be imported, provide a fallback stub to avoid crashes.
    def register_all_handlers(dp):
        # fallback: no-op registration (real implementation is in handlers/register_all_handlers.py)
        return None
    __all__ = ["register_all_handlers"] + _TOP_MODULES + ["admin_broadcast"]
