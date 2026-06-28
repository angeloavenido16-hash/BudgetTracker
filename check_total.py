import sys, os
sys.path.insert(0, r'c:\Users\AAvenido\Documents\Budget Tracker App')
import openpyxl

wb = openpyxl.load_workbook(
    r'c:\Users\AAvenido\Documents\Budget Tracker App\BudgetTracker_Final_Update.xlsm',
    keep_vba=True, data_only=True
)

ws = wb["Total Amount"]
print("=== Total Amount Sheet (Col A=Label, B=Amount, C=TotalExpenses, D=AfterExpenses) ===")
for row in ws.iter_rows(min_row=1, max_row=50, values_only=True):
    if row[0] is not None:
        print(f"  A={str(row[0]):<40}  B={row[1]}")
