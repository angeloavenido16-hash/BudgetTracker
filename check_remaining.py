import sys
sys.path.insert(0, r'c:/Users/AAvenido/Documents/Budget Tracker App')
import database as db

funds = db.get_funds()
print(f"{'Fund':<38} {'Income':>12} {'Remaining':>12}")
print('-' * 64)
for f in funds[:15]:
    s = db.get_fund_summary(f['id'])
    name = f['name'][:38]
    print(f"{name:<38} {s['income']:>12,.2f} {s['remaining']:>12,.2f}")
