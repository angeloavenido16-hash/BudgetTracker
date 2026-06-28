import sys, os
sys.path.insert(0, r'c:\Users\AAvenido\Documents\Budget Tracker App')
import openpyxl, database as db

wb = openpyxl.load_workbook(
    r'c:\Users\AAvenido\Documents\Budget Tracker App\BudgetTracker_Final_Update.xlsm',
    keep_vba=True, data_only=True
)

# Check Total Amount cols B, C, D for first 5 salary rows
ws = wb["Total Amount"]
print("Excel Total Amount — Col B=Amount, C=TotalExpenses, D=AfterExpenses")
print(f"{'Fund':<30} {'B(Amount)':>12} {'C(Expenses)':>13} {'D(Remaining)':>13}")
print("-"*70)
for row in ws.iter_rows(min_row=12, max_row=17, values_only=True):
    a, b, c, d = row[0], row[1], row[2], row[3]
    if a:
        print(f"{str(a):<30} {b or 0:>12,.2f} {c or 0:>13,.2f} {d or 0:>13,.2f}")

print()

# Show what the APP currently computes for the same funds
print("APP computed values:")
print(f"{'Fund':<30} {'Amount':>12} {'Expenses':>13} {'Remaining':>13}")
print("-"*70)
for f in db.get_funds():
    if "Salary" in f["name"] and "2025" in f["name"]:
        s = db.get_fund_summary(f["id"])
        print(f"{f['name']:<30} {s['income']:>12,.2f} {s['expenses']:>13,.2f} {s['remaining']:>13,.2f}")
    if f["name"] == "02/27/2025 Salary":
        print()
        print("  [02-27-25 raw transactions]")
        txns = db.get_transactions(f["id"])
        for t in txns:
            print(f"    {t['category']:<25} {t['amount']:>10,.2f}")
        print(f"  SUM = {sum(t['amount'] for t in txns):,.2f}")
        break
