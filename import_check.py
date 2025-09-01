import importlib
mods = ['handlers.tariffs','handlers.purchase','handlers.my_tariff','handlers.ask_question','handlers.admin_contact']
errors = False
for m in mods:
    try:
        importlib.import_module(m)
        print('OK', m)
    except Exception as e:
        print('ERR', m, type(e).__name__, e)
        errors = True
if errors:
    raise SystemExit(1)
print('ALL IMPORTS OK')
