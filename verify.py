import sys
sys.path.insert(0, r'c:\Users\AAvenido\Documents\Budget Tracker App')
import database as db

# Expected from Total Amount sheet
expected = {
    "Maya Account":              22900.00,
    "Maya Account 2":            300.00,
    "ESPP (Bora Trip)":          76941.92,
    "ESPP Expenses 2":           110375.59,
    "13.5 Month Pay (FY25)":     14491.15,
    "13th Month Pay (FY25)":     30431.42,
    "13.5 Month Pay (FY26)":     16857.86,
    "Corporate Bonus 1Q/2Q25":   8757.94,
    "Corporate Bonus 3Q/4Q25":   19391.84,
    "Corporate Bonus 1Q/2Q26":   26215.02,
}

print(f"{'Fund':<35} {'Expected':>12} {'Actual':>12} {'Match':>6}")
print("-" * 68)
all_ok = True
for f in db.get_funds():
    exp = expected.get(f['name'])
    if exp is None:
        continue
    match = abs(f['amount'] - exp) < 0.01
    if not match:
        all_ok = False
    print(f"{f['name']:<35} {exp:>12,.2f} {f['amount']:>12,.2f} {'✔' if match else '✘ MISMATCH':>6}")

print()
print("All special funds match!" if all_ok else "⚠ Some funds still mismatch!")
