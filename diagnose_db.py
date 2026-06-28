import sqlite3
conn = sqlite3.connect(r'c:/Users/AAvenido/Documents/Budget Tracker App/budget_tracker.db')

pos_sav = conn.execute(
    'SELECT f.name, t.amount, t.remarks FROM transactions t '
    'JOIN funds f ON f.id=t.fund_id '
    'WHERE LOWER(t.category)="savings" AND t.amount>0 LIMIT 8'
).fetchall()
print('POSITIVE savings (sample):')
for r in pos_sav:
    print(f'  {r[0]:<32} {r[1]:>10,.2f}  {r[2]}')

pos_by_fund = conn.execute(
    'SELECT f.name, COUNT(*) as cnt, SUM(t.amount) as total FROM transactions t '
    'JOIN funds f ON f.id=t.fund_id '
    'WHERE LOWER(t.category)="savings" AND t.amount>0 GROUP BY f.id'
).fetchall()
print()
print('Funds with POSITIVE savings entries:')
for r in pos_by_fund:
    print(f'  {r[0]:<35} cnt={r[1]}  total={r[2]:,.2f}')

total_income = conn.execute('SELECT COALESCE(SUM(amount),0) FROM funds').fetchone()[0]
all_txn = conn.execute('SELECT COALESCE(SUM(amount),0) FROM transactions').fetchone()[0]
print()
print('=== CORRECT NET REMAINING ===')
print(f'Total income:   {total_income:,.2f}')
print(f'SUM all txns:   {all_txn:,.2f}')
print(f'Net remaining:  {total_income - all_txn:,.2f}')

real_expenses = conn.execute(
    'SELECT COALESCE(SUM(amount),0) FROM transactions '
    'WHERE amount > 0 AND LOWER(category) NOT IN ("savings","carry over","carry_over","received")'
).fetchone()[0]
real_savings_neg = conn.execute(
    'SELECT COALESCE(SUM(ABS(amount)),0) FROM transactions '
    'WHERE LOWER(category)="savings" AND amount < 0'
).fetchone()[0]
real_savings_pos = conn.execute(
    'SELECT COALESCE(SUM(amount),0) FROM transactions '
    'WHERE LOWER(category)="savings" AND amount > 0'
).fetchone()[0]
print()
print('=== PROPOSED DASHBOARD BREAKDOWN ===')
print(f'Real expenses (pos, excl. savings):    {real_expenses:,.2f}')
print(f'Savings OUT (neg savings abs value):    {real_savings_neg:,.2f}')
print(f'Savings IN  (pos savings — adjustments):{real_savings_pos:,.2f}')
conn.close()
