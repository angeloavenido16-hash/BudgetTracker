import { useState } from "react";
import { peso } from "../components/StatCard";
import {
  useReportOverview,
  useCategoryStats,
  useFundFlows,
  useTransactionYears,
} from "../hooks/useReports";
import { useFunds } from "../hooks/useFunds";
import type { ReportFilters, ReportOverview } from "../api/types";

/**
 * Reports — numbers-first statistical report (mirrors the desktop redesign).
 *
 * Three tabs, all driven by the shared Year / Month / Fund filters:
 *   • Overview       – headline stats + auto-generated insights
 *   • Category Stats – per-category spend / count / average / share / biggest
 *   • Ins & Outs     – per-fund money in (+) vs out (−) and net flow
 *
 * Charts deliberately live on the Dashboard, not here (same split as desktop).
 */

type Tab = "overview" | "category" | "flows";

const MONTHS: { label: string; value: string }[] = [
  { label: "All", value: "All" },
  { label: "January", value: "01" }, { label: "February", value: "02" },
  { label: "March", value: "03" }, { label: "April", value: "04" },
  { label: "May", value: "05" }, { label: "June", value: "06" },
  { label: "July", value: "07" }, { label: "August", value: "08" },
  { label: "September", value: "09" }, { label: "October", value: "10" },
  { label: "November", value: "11" }, { label: "December", value: "12" },
];

function fmtMonth(key: string): string {
  const [year, mon] = key.split("-");
  const names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                 "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const idx = parseInt(mon, 10) - 1;
  return names[idx] ? `${names[idx]} ${year}` : key;
}

export default function Reports() {
  const [tab, setTab] = useState<Tab>("overview");
  const [year, setYear] = useState("All");
  const [month, setMonth] = useState("All");
  const [fundName, setFundName] = useState("All");

  const years = useTransactionYears();
  const funds = useFunds();

  const fundId =
    fundName === "All"
      ? undefined
      : funds.data?.find((f) => f.name === fundName)?.id;
  const filters: ReportFilters = { year, month, fundId };

  const monthLabel =
    MONTHS.find((m) => m.value === month)?.label ?? "All";
  const scope = `Showing: ${year === "All" ? "All years" : year}  •  ${
    month === "All" ? "all months" : monthLabel
  }  •  ${fundName === "All" ? "all funds" : fundName}`;

  return (
    <div>
      <h2 className="page-title">Reports</h2>

      {/* Filter bar */}
      <div className="filter-bar">
        <label>
          Year:&nbsp;
          <select value={year} onChange={(e) => setYear(e.target.value)}>
            <option value="All">All</option>
            {(years.data ?? []).map((y) => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>
        </label>
        <label>
          Month:&nbsp;
          <select value={month} onChange={(e) => setMonth(e.target.value)}>
            {MONTHS.map((m) => (
              <option key={m.value} value={m.value}>{m.label}</option>
            ))}
          </select>
        </label>
        <label>
          Fund:&nbsp;
          <select value={fundName} onChange={(e) => setFundName(e.target.value)}>
            <option value="All">All</option>
            {(funds.data ?? []).map((f) => (
              <option key={f.id} value={f.name}>{f.name}</option>
            ))}
          </select>
        </label>
        <span className="scope-label">{scope}</span>
      </div>

      {/* Tab strip */}
      <div className="tab-strip">
        <button className={tab === "overview" ? "active" : ""}
                onClick={() => setTab("overview")}>📊 Overview</button>
        <button className={tab === "category" ? "active" : ""}
                onClick={() => setTab("category")}>🏷 Category Stats</button>
        <button className={tab === "flows" ? "active" : ""}
                onClick={() => setTab("flows")}>💸 Ins &amp; Outs</button>
      </div>

      {tab === "overview" && <OverviewTab filters={filters} />}
      {tab === "category" && <CategoryTab filters={filters} />}
      {tab === "flows" && <FlowsTab filters={filters} />}
    </div>
  );
}

// ── Tab 1: Overview ─────────────────────────────────────────────────────────
function OverviewTab({ filters }: { filters: ReportFilters }) {
  const { data: o, isLoading, isError } = useReportOverview(filters);
  if (isLoading) return <p>Loading…</p>;
  if (isError || !o) return <p>Could not load overview.</p>;
  if (!o.txn_count) return <p>No transactions match these filters.</p>;

  return (
    <div>
      <div className="stat-grid">
        <Stat label="Total Spent" value={peso(o.total_spent)} />
        <Stat label="Avg / Month" value={peso(o.avg_monthly)} />
        <Stat label="Avg / Transaction" value={peso(o.avg_txn)} />
        <Stat label="Transactions" value={o.txn_count.toLocaleString()} />
        <Stat label="Savings Booked" value={peso(o.savings)} />
      </div>

      <div className="insights">
        <h3>💡 Insights</h3>
        {buildInsights(o).map((line, i) => (
          <p key={i}>{line}</p>
        ))}
      </div>
    </div>
  );
}

function buildInsights(o: ReportOverview): string[] {
  const lines: string[] = [];
  if (o.biggest) {
    const date = (o.biggest.txn_date ?? "").slice(0, 10);
    lines.push(
      `🔺 Biggest expense: ${peso(o.biggest.amount)} on “${o.biggest.category}”` +
        ` (${o.biggest.fund_name ?? ""}${date ? ", " + date : ""}).`
    );
  }
  if (o.top_category) {
    lines.push(
      `🏷 Top category: “${o.top_category[0]}” at ${peso(o.top_category[1])} ` +
        `— ${o.top_category_share.toFixed(0)}% of all spending.`
    );
  }
  if (o.most_frequent) {
    lines.push(`🔁 Most frequent: “${o.most_frequent[0]}” with ${o.most_frequent[1]} transactions.`);
  }
  if (o.busiest_month) {
    lines.push(`📈 Busiest month: ${fmtMonth(o.busiest_month[0])} (${peso(o.busiest_month[1])} spent).`);
  }
  if (o.quietest_month && o.active_months > 1) {
    lines.push(`📉 Quietest month: ${fmtMonth(o.quietest_month[0])} (${peso(o.quietest_month[1])} spent).`);
  }
  if (o.mom_change != null && o.latest_month) {
    const word = o.mom_change > 0 ? "up" : "down";
    const arrow = o.mom_change > 0 ? "⬆️" : "⬇️";
    lines.push(
      `${arrow} ${fmtMonth(o.latest_month[0])} spending is ${word} ` +
        `${Math.abs(o.mom_change).toFixed(0)}% vs the previous month.`
    );
  }
  lines.push(
    `📅 Activity spread across ${o.active_months} ` +
      `month${o.active_months !== 1 ? "s" : ""}.`
  );
  return lines;
}

// ── Tab 2: Category Stats ───────────────────────────────────────────────────
function CategoryTab({ filters }: { filters: ReportFilters }) {
  const { data: rows, isLoading, isError } = useCategoryStats(filters);
  if (isLoading) return <p>Loading…</p>;
  if (isError || !rows) return <p>Could not load category stats.</p>;
  if (!rows.length) return <p>No spending categories match these filters.</p>;

  return (
    <table>
      <thead>
        <tr>
          <th>Category</th><th>Total Spent</th><th>Txns</th>
          <th>Average</th><th>% Share</th><th>Biggest</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => (
          <tr key={r.category}
              style={{ color: r.share >= 15 ? "var(--red)" : undefined }}>
            <td>{r.category}</td>
            <td>{peso(r.total)}</td>
            <td>{r.count.toLocaleString()}</td>
            <td>{peso(r.avg)}</td>
            <td>{r.share.toFixed(1)}%</td>
            <td>{peso(r.max)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

// ── Tab 3: Ins & Outs ───────────────────────────────────────────────────────
function FlowsTab({ filters }: { filters: ReportFilters }) {
  const { data: all, isLoading, isError } = useFundFlows(filters);
  if (isLoading) return <p>Loading…</p>;
  if (isError || !all) return <p>Could not load fund flows.</p>;
  const rows = all.filter((r) => r.count > 0);
  if (!rows.length) return <p>No fund activity matches this filter.</p>;

  const totIn = rows.reduce((s, r) => s + r.in_flow, 0);
  const totOut = rows.reduce((s, r) => s + r.out_flow, 0);

  return (
    <div>
      <div className="stat-grid">
        <Stat label="Total In (+)" value={peso(totIn)} />
        <Stat label="Total Out (−)" value={peso(totOut)} />
        <Stat label="Net Flow" value={peso(totIn - totOut)} />
      </div>
      <table>
        <thead>
          <tr><th>Fund</th><th>In (+)</th><th>Out (−)</th><th>Net</th><th>Txns</th></tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.id}>
              <td>{r.name}</td>
              <td>{peso(r.in_flow)}</td>
              <td>{peso(r.out_flow)}</td>
              <td style={{ color: r.net >= 0 ? "var(--green)" : "var(--red)" }}>
                {(r.net >= 0 ? "+" : "−") + peso(Math.abs(r.net))}
              </td>
              <td>{r.count.toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ── Tiny presentational helper ──────────────────────────────────────────────
function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="stat-card">
      <div className="label">{label}</div>
      <div className="value">{value}</div>
    </div>
  );
}
