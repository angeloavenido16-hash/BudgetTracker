import { useState } from "react";
import {
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend, Area, AreaChart, BarChart, Bar,
} from "recharts";
import StatCard, { peso } from "../components/StatCard";
import {
  useDashboard,
  useSpendingOverTime,
  useExpenseByCategory,
  useCategoryOverTime,
} from "../hooks/useDashboard";
import { useFunds } from "../hooks/useFunds";
import { useCategories } from "../hooks/useCategories";
import { useTransactionYears } from "../hooks/useReports";
import { missingColor } from "../theme";

const PIE_COLORS = ["#e94560", "#533483", "#2ecc71", "#f39c12", "#3498db", "#9b59b6", "#e67e22"];
const SKIP_CATS = new Set(["savings", "carry over", "carry_over", "payment", "interest", "tax", "refund"]);

function fmtMonth(key: string): string {
  const [y, m] = key.split("-");
  const names = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
  const i = parseInt(m, 10) - 1;
  return names[i] ? `${names[i]} ${y}` : key;
}

/**
 * Dashboard — headline cards + year filter, mirroring the desktop view.
 *
 * Cards: Total Income · Total Expenses · Total Savings · Net Remaining ·
 *        BPI Balance · Missing Expenses · Salary · Bonus · ESPP.
 *
 * Missing Expenses = bpi_balance − non_other_remaining. RED when positive
 * (unaccounted bank money) and GREEN when ≤ 0 — matching the desktop coloring.
 */
export default function Dashboard() {
  const [year, setYear] = useState("All");
  const { data, isLoading, isError } = useDashboard(year);
  const present = useDashboard("All"); // BPI + Missing always reflect the present
  const funds = useFunds();
  const years = useTransactionYears();

  if (isLoading) return <p>Loading…</p>;
  if (isError || !data) return <p>Could not load dashboard. Is the API running?</p>;

  // Missing Expenses: multi-color — green = 0, yellow > 0, red < 0. Uses present.
  const missing = present.data?.missing_expenses ?? 0;
  const bpi = present.data?.bpi_balance ?? 0;

  // Fixed income per primary fund type — scoped to the selected year by cutoff.
  const sumType = (t: string) =>
    (funds.data ?? [])
      .filter((f) => f.fund_type === t && (year === "All" || (f.cutoff_date ?? "").slice(0, 4) === year))
      .reduce((s, f) => s + f.amount, 0);
  const salary = sumType("salary");
  const bonus = sumType("bonus");
  const espp = sumType("espp");

  return (
    <div>
      <div className="page-head">
        <h2 className="page-title">Dashboard</h2>
        <label className="dash-filter">
          Year:&nbsp;
          <select value={year} onChange={(e) => setYear(e.target.value)}>
            <option value="All">All</option>
            {(years.data ?? []).map((y) => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>
        </label>
      </div>
      <div className="stat-grid">
        <StatCard label="Total Income" value={data.total_income} />
        <StatCard label="Total Expenses" value={data.total_expenses} />
        <StatCard label="Total Savings" value={data.total_savings} />
        <StatCard label="Net Remaining" value={data.net_remaining} colorBySign />
        <StatCard label="💵 Salary" value={salary} />
        <StatCard label="🎁 Bonus" value={bonus} />
        <StatCard label="📈 ESPP" value={espp} />
      </div>

      <div className="chart-row">
        <div className="chart-card">
          <h3>Monthly Spending</h3>
          <SpendingChart year={year} />
        </div>
        <div className="chart-card">
          <h3>Top Expense Categories</h3>
          <CategoryPie year={year} />
        </div>
      </div>

      <CategoryHistogram year={year} sign="out" title="Outflow per Month" match="budget" color="var(--accent)" />
      <CategoryHistogram year={year} sign="in" title="Inflow per Month" match="savings" color="#2ecc71" />

      {/* Live bank figures — always present, never affected by the year filter */}
      <div className="present-band">
        <span className="present-tag">Current — not year-filtered</span>
        <div className="present-cards">
          <StatCard label="BPI Balance" value={bpi} />
          <div className="stat-card">
            <div className="label">Missing Expenses</div>
            <div className="value" style={{ color: missingColor(missing) }}>
              {peso(missing)}
            </div>
          </div>
        </div>
      </div>

      <p style={{ color: "var(--text-muted)", fontSize: 13 }}>
        {data.fund_count} funds tracked.
      </p>
    </div>
  );
}

/** Area/line chart of monthly spend (year-filtered). */
function SpendingChart({ year }: { year: string }) {
  const { data, isLoading } = useSpendingOverTime(year);
  if (isLoading) return <p className="settings-empty">Loading…</p>;
  if (!data || data.length === 0) return <p className="settings-empty">No data yet.</p>;
  const rows = data.map((d) => ({ month: fmtMonth(d.month), total: d.total }));
  return (
    <ResponsiveContainer width="100%" height={260}>
      <AreaChart data={rows} margin={{ top: 8, right: 12, bottom: 0, left: -10 }}>
        <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" />
        <XAxis dataKey="month" tick={{ fill: "var(--text-muted)", fontSize: 11 }} />
        <YAxis tick={{ fill: "var(--text-muted)", fontSize: 11 }} />
        <Tooltip formatter={(v: number) => peso(v)} contentStyle={{ background: "var(--surface)", border: "1px solid var(--border)" }} />
        <Area type="monotone" dataKey="total" stroke="var(--accent)" fill="var(--accent)" fillOpacity={0.15} strokeWidth={2} />
      </AreaChart>
    </ResponsiveContainer>
  );
}

/** Pie of top-7 expense categories (year-filtered, system cats skipped). */
function CategoryPie({ year }: { year: string }) {
  const { data, isLoading } = useExpenseByCategory(year);
  if (isLoading) return <p className="settings-empty">Loading…</p>;
  const top = (data ?? []).filter((d) => !SKIP_CATS.has(d.category.toLowerCase()) && d.total > 0).slice(0, 7);
  if (top.length === 0) return <p className="settings-empty">No data yet.</p>;
  return (
    <ResponsiveContainer width="100%" height={260}>
      <PieChart>
        <Pie data={top} dataKey="total" nameKey="category" cx="50%" cy="45%" outerRadius={80}>
          {top.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
        </Pie>
        <Tooltip formatter={(v: number) => peso(v)} contentStyle={{ background: "var(--surface)", border: "1px solid var(--border)" }} />
        <Legend wrapperStyle={{ fontSize: 11, color: "var(--text-muted)" }} />
      </PieChart>
    </ResponsiveContainer>
  );
}

/** Monthly histogram for ONE chosen category, restricted to a flow direction.
 *  `sign` "out" = spending (positive), "in" = credits (negative shown as +).
 *  Picks a sensible default category via `match`, falls back to first. */
function CategoryHistogram({
  year, sign, title, match, color,
}: {
  year: string;
  sign: "in" | "out";
  title: string;
  match: string;
  color: string;
}) {
  const cats = useCategories();
  const [cat, setCat] = useState("");
  const fallback = cats.data?.find((c) => c.toLowerCase().includes(match)) ?? cats.data?.[0] ?? "";
  const chosen = cat || fallback;
  const { data, isLoading } = useCategoryOverTime(chosen, year, sign);
  const rows = (data ?? []).map((d) => ({ month: fmtMonth(d.month), total: d.total }));
  const total = rows.reduce((s, r) => s + r.total, 0);
  const avg = rows.length ? total / rows.length : 0;

  return (
    <div className="chart-card" style={{ marginBottom: 18 }}>
      <div className="page-head" style={{ marginBottom: 8 }}>
        <h3>{title}{rows.length ? ` — ${peso(total)} total · ${peso(avg)}/mo` : ""}</h3>
        <select className="dash-filter" value={chosen} onChange={(e) => setCat(e.target.value)}>
          {(cats.data ?? []).map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>
      {isLoading ? (
        <p className="settings-empty">Loading…</p>
      ) : rows.length === 0 ? (
        <p className="settings-empty">No {sign === "in" ? "inflow" : "outflow"} for “{chosen}” yet.</p>
      ) : (
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={rows} margin={{ top: 8, right: 12, bottom: 0, left: -10 }}>
            <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" />
            <XAxis dataKey="month" tick={{ fill: "var(--text-muted)", fontSize: 11 }} />
            <YAxis tick={{ fill: "var(--text-muted)", fontSize: 11 }} />
            <Tooltip formatter={(v: number) => peso(v)} contentStyle={{ background: "var(--surface)", border: "1px solid var(--border)" }} cursor={{ fill: "rgba(255,255,255,0.04)" }} />
            <Bar dataKey="total" fill={color} radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
