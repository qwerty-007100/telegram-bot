PRICE_MAP = {
    ("pro", "week"): 19000,
    ("pro", "month"): 59000,
    ("premium", "week"): 29000,
    ("premium", "month"): 99000,
    ("pregnancy", "month1"): 79000,
    ("pregnancy", "month9"): 349000,
    ("planning", "week"): 59000,
    ("planning", "month"): 199000,
}

HUMAN_LABEL = {
    ("pro", "week"): "Pro — 1 haftalik",
    ("pro", "month"): "Pro — 1 oylik",
    ("premium", "week"): "Premium — 1 haftalik",
    ("premium", "month"): "Premium — 1 oylik",
    ("pregnancy", "month1"): "Homiladorlik — 1 oylik",
    ("pregnancy", "month9"): "Homiladorlik — 9 oylik",
    ("planning", "week"): "Farzand rejalash — 1 haftalik",
    ("planning", "month"): "Farzand rejalash — 1 oylik",
}

DURATION_DAYS = {
    "week": 7,
    "month": 30,
    "month1": 30,
    "month9": 280,
}

def price_of(tariff_code: str, plan_code: str):
    return PRICE_MAP.get((tariff_code, plan_code))

def human_name(tariff_code: str, plan_code: str):
    return HUMAN_LABEL.get((tariff_code, plan_code))

def duration_days(plan_code: str):
    return DURATION_DAYS.get(plan_code)
