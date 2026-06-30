import { useMemo, useState, type ReactNode } from "react";
import Spinner from "../components/Spinner";
import { peso } from "../components/StatCard";
import {
  useReportOverview,
  useCategoryStats,
  useFundFlows,
  useTransactionYears,
} from "../hooks/useReports";
import { useFunds } from "../hooks/useFunds";
import type { ReportFilters, ReportOverview } from "../api/types";
import { BarChart3, Tags, ArrowRightLeft, Lightbulb, TrendingUp, TrendingDown, RefreshCw, Calendar, TriangleAlert } from "lucide-react";

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
      <div className="page-head">
        <h2 className="page-title">Reports</h2>
      </div>

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
                onClick={() => setTab("overview")}><span className="icon-text"><BarChart3 size={16} /> Overview</span></button>
        <button className={tab === "category" ? "active" : ""}
                onClick={() => setTab("category")}><span className="icon-text"><Tags size={16} /> Category Stats</span></button>
        <button className={tab === "flows" ? "active" : ""}
                onClick={() => setTab("flows")}><span className="icon-text"><ArrowRightLeft size={16} /> Ins &amp; Outs</span></button>
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
  if (isLoading) return <Spinner />;
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
        <h3><span className="icon-text"><Lightbulb size={18} /> Insights</span></h3>
        {buildInsights(o).map((line, i) => (
          <p key={i}>{line}</p>
        ))}
      </div>
    </div>
  );
}

function buildInsights(o: ReportOverview): ReactNode[] {
  const lines: ReactNode[] = [];
  if (o.biggest) {
    const date = (o.biggest.txn_date ?? "").slice(0, 10);
    lines.push(
      <span className="icon-text"><TriangleAlert size={14} /> Biggest expense: {peso(o.biggest.amount)} on “{o.biggest.category}”{(o.biggest.fund_name ?? date) ? ` (${o.biggest.fund_name ?? ""}${date ? ", " + date : ""})` : ""}.</span>
    );
  }
  if (o.top_category) {
    lines.push(
      <span className="icon-text"><Tags size={14} /> Top category: “{o.top_category[0]}” at {peso(o.top_category[1])} — {o.top_category_share.toFixed(0)}% of all spending.</span>
    );
  }
  if (o.most_frequent) {
    lines.push(<span className="icon-text"><RefreshCw size={14} /> Most frequent: “{o.most_frequent[0]}” with {o.most_frequent[1]} transactions.</span>);
  }
  if (o.busiest_month) {
    lines.push(<span className="icon-text"><TrendingUp size={14} /> Busiest month: {fmtMonth(o.busiest_month[0])} ({peso(o.busiest_month[1])} spent).</span>);
  }
  if (o.quietest_month && o.active_months > 1) {
    lines.push(<span className="icon-text"><TrendingDown size={14} /> Quietest month: {fmtMonth(o.quietest_month[0])} ({peso(o.quietest_month[1])} spent).</span>);
  }
  if (o.mom_change != null && o.latest_month) {
    const word = o.mom_change > 0 ? "up" : "down";
    lines.push(
      <span className="icon-text">{o.mom_change > 0 ? <TrendingUp size={14} /> : <TrendingDown size={14} />} {fmtMonth(o.latest_month[0])} spending is {word} {Math.abs(o.mom_change).toFixed(0)}% vs the previous month.</span>
    );
  }
  lines.push(
    <span className="icon-text"><Calendar size={14} /> Activity spread across {o.active_months} month{o.active_months !== 1 ? "s" : ""}.</span>
  );
  return lines;
}

// ── Tab 2: Category Stats ───────────────────────────────────────────────────
type CatSortCol = "category" | "total" | "count" | "avg" | "share" | "max";
function CategoryTab({ filters }: { filters: ReportFilters }) {
  const { data: rows, isLoading, isError } = useCategoryStats(filters);
  const [catSortCol, setCatSortCol] = useState<CatSortCol>("total");
  const [catSortAsc, setCatSortAsc] = useState(false);
  const sorted = useMemo(() => {
    return [...(rows ?? [])].sort((a, b) => {
      const ka = a[catSortCol], kb = b[catSortCol];
      const cmp = ka < kb ? -1 : ka > kb ? 1 : 0;
      return catSortAsc ? cmp : -cmp;
    });
  }, [rows, catSortCol, catSortAsc]);
  const catSortBy = (c: CatSortCol) => c === catSortCol ? setCatSortAsc((a) => !a) : (setCatSortCol(c), setCatSortAsc(false));
  const catArrow = (c: CatSortCol) => (catSortCol === c ? (catSortAsc ? " ▲" : " ▼") : "");

  if (isLoading) return <Spinner />;
  if (isError || !rows) return <p>Could not load category stats.</p>;
  if (!rows.length) return <p>No spending categories match these filters.</p>;

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th className="sortable" onClick={() => catSortBy("category")}>Category{catArrow("category")}</th>
            <th className="sortable" onClick={() => catSortBy("total")}>Total Spent{catArrow("total")}</th>
            <th className="sortable" onClick={() => catSortBy("count")}>Txns{catArrow("count")}</th>
            <th className="sortable" onClick={() => catSortBy("avg")}>Average{catArrow("avg")}</th>
            <th className="sortable" onClick={() => catSortBy("share")}>% Share{catArrow("share")}</th>
            <th className="sortable" onClick={() => catSortBy("max")}>Biggest{catArrow("max")}</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((r) => (
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
    </div>
  );
}

// ── Tab 3: Ins & Outs ───────────────────────────────────────────────────────
type FlowSortCol = "name" | "in_flow" | "out_flow" | "net" | "count";
function FlowsTab({ filters }: { filters: ReportFilters }) {
  const { data: all, isLoading, isError } = useFundFlows(filters);
  const [flowSortCol, setFlowSortCol] = useState<FlowSortCol>("net");
  const [flowSortAsc, setFlowSortAsc] = useState(false);
  const active = useMemo(() => (all ?? []).filter((r) => r.count > 0), [all]);
  const rows = useMemo(() => {
    return [...active].sort((a, b) => {
      const ka = a[flowSortCol], kb = b[flowSortCol];
      const cmp = ka < kb ? -1 : ka > kb ? 1 : 0;
      return flowSortAsc ? cmp : -cmp;
    });
  }, [active, flowSortCol, flowSortAsc]);
  const flowSortBy = (c: FlowSortCol) => c === flowSortCol ? setFlowSortAsc((a) => !a) : (setFlowSortCol(c), setFlowSortAsc(false));
  const flowArrow = (c: FlowSortCol) => (flowSortCol === c ? (flowSortAsc ? " ▲" : " ▼") : "");

  if (isLoading) return <Spinner />;
  if (isError || !all) return <p>Could not load fund flows.</p>;
  if (!active.length) return <p>No fund activity matches this filter.</p>;

  const totIn = rows.reduce((s, r) => s + r.in_flow, 0);
  const totOut = rows.reduce((s, r) => s + r.out_flow, 0);

  return (
    <div>
      <div className="stat-grid">
        <Stat label="Total In (+)" value={peso(totIn)} />
        <Stat label="Total Out (−)" value={peso(totOut)} />
        <Stat label="Net Flow" value={peso(totIn - totOut)} />
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th className="sortable" onClick={() => flowSortBy("name")}>Fund{flowArrow("name")}</th>
              <th className="sortable" onClick={() => flowSortBy("in_flow")}>In (+){flowArrow("in_flow")}</th>
              <th className="sortable" onClick={() => flowSortBy("out_flow")}>Out (−){flowArrow("out_flow")}</th>
              <th className="sortable" onClick={() => flowSortBy("net")}>Net{flowArrow("net")}</th>
              <th className="sortable" onClick={() => flowSortBy("count")}>Txns{flowArrow("count")}</th>
            </tr>
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
