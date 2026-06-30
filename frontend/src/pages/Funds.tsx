import { useMemo, useState, type ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import {
  useFunds,
  useFundSummaries,
  useCreateFund,
  useUpdateFund,
  useDeleteFund,
} from "../hooks/useFunds";
import Spinner from "../components/Spinner";
import { peso } from "../components/StatCard";
import { FUND_TYPE_LABELS, remainingColor } from "../theme";
import Modal from "../components/Modal";
import { useToast } from "../components/Toast";
import type { Fund, FundType, FundSummary } from "../api/types";
import { Eye, EyeOff, DollarSign, Gift, TrendingUp, Building2, Lock } from "lucide-react";

const FUND_TYPE_ICONS: Record<string, ReactNode> = {
  salary: <DollarSign size={14} />,
  bonus: <Gift size={14} />,
  espp: <TrendingUp size={14} />,
  other: <Building2 size={14} />,
};

const FILTERS: { value: string; label: string }[] = [
  { value: "all", label: "All" },
  { value: "salary", label: "Salary" },
  { value: "bonus", label: "Bonus" },
  { value: "espp", label: "ESPP" },
  { value: "other", label: "Other" },
];

const PAGE_SIZE = 50;

// Sortable columns (index → summary/fund key). null = static action col.
type SortCol = "name" | "fund_type" | "cutoff_date" | "amount" | "expenses" | "savings" | "house" | "carry_over" | "remaining";

/**
 * Income Funds — table of funds with their computed summaries.
 * Summary numbers come from GET /funds/summaries (server-side formulas).
 * Mirrors the desktop view: type filter + clickable-header sort with the
 * hierarchy primary → Remaining DESC → Cutoff DESC → Name ASC.
 */
export default function Funds() {
  const funds = useFunds();
  const summaries = useFundSummaries();
  const del = useDeleteFund();
  const { toast } = useToast();
  const navigate = useNavigate();
  const [editing, setEditing] = useState<Fund | "new" | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Fund | null>(null);
  const [filter, setFilter] = useState("all");
  const [yearFilter, setYearFilter] = useState("all");
  const [page, setPage] = useState(0);
  const [sortCol, setSortCol] = useState<SortCol>("remaining");
  const [sortAsc, setSortAsc] = useState(false); // Remaining DESC default
  const [masked, setMasked] = useState(() => localStorage.getItem("mask") === "1");

  const toggleMask = () =>
    setMasked((m) => { localStorage.setItem("mask", m ? "0" : "1"); return !m; });
  const money = (v: number) => (masked ? "₱ ••••" : peso(v));

  const sums: Record<number, FundSummary> = summaries.data ?? {};

  // Distinct cutoff years (newest first) for the year dropdown.
  const fundYears = useMemo(() => {
    const ys = new Set<string>();
    (funds.data ?? []).forEach((f) => { const y = (f.cutoff_date ?? "").slice(0, 4); if (y) ys.add(y); });
    return [...ys].sort().reverse();
  }, [funds.data]);

  const sorted = useMemo(() => {
    let list = funds.data ?? [];
    if (filter !== "all") list = list.filter((f) => f.fund_type === filter);
    if (yearFilter !== "all") list = list.filter((f) => (f.cutoff_date ?? "").slice(0, 4) === yearFilter);
    const key = (f: Fund): number | string => {
      const s = sums[f.id];
      switch (sortCol) {
        case "name": return f.name.toLowerCase();
        case "fund_type": return f.fund_type;
        case "cutoff_date": return f.cutoff_date ?? "";
        case "amount": return f.amount;
        case "expenses": return s?.expenses ?? 0;
        case "savings": return s?.savings ?? 0;
        case "house": return s?.house ?? 0;
        case "carry_over": return s?.carry_over ?? 0;
        default: return s?.remaining ?? 0;
      }
    };
    // Hierarchy: Name ASC → Cutoff DESC → Remaining DESC → primary col.
    return [...list].sort((a, b) => {
      const ka = key(a), kb = key(b);
      const cmp = ka < kb ? -1 : ka > kb ? 1 : 0;
      return sortAsc ? cmp : -cmp;
    });
  }, [funds.data, sums, filter, yearFilter, sortCol, sortAsc]);

  const pageCount = Math.ceil(sorted.length / PAGE_SIZE);
  const safePage = Math.min(page, Math.max(0, pageCount - 1));
  const rows = sorted.slice(safePage * PAGE_SIZE, safePage * PAGE_SIZE + PAGE_SIZE);

  if (funds.isLoading || summaries.isLoading) return <Spinner />;
  if (funds.isError || !funds.data) return <p>Could not load funds.</p>;

  const sortBy = (col: SortCol) => {
    if (col === sortCol) setSortAsc((a) => !a);
    else { setSortCol(col); setSortAsc(true); }
  };
  const arrow = (col: SortCol) => (sortCol === col ? (sortAsc ? " ▲" : " ▼") : "");

  return (
    <div>
      <div className="page-head">
        <h2 className="page-title">Income Funds</h2>
      </div>
      <div className="filter-bar">
        <label>
          Filter:&nbsp;
          <select value={filter} onChange={(e) => { setFilter(e.target.value); setPage(0); }}>
            {FILTERS.map((f) => (
              <option key={f.value} value={f.value}>{f.label}</option>
            ))}
          </select>
        </label>
        <label>
          Year:&nbsp;
          <select value={yearFilter} onChange={(e) => { setYearFilter(e.target.value); setPage(0); }}>
            <option value="all">All</option>
            {fundYears.map((y) => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>
        </label>
        <span className="scope-label">{sorted.length} funds</span>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th className="sortable" onClick={() => sortBy("name")}>Name{arrow("name")}</th>
              <th className="sortable" onClick={() => sortBy("fund_type")}>Type{arrow("fund_type")}</th>
              <th className="sortable" onClick={() => sortBy("cutoff_date")}>Cutoff{arrow("cutoff_date")}</th>
              <th className="sortable" onClick={() => sortBy("amount")}>Income{arrow("amount")}</th>
              <th className="sortable" onClick={() => sortBy("expenses")}>Expenses{arrow("expenses")}</th>
              <th className="sortable" onClick={() => sortBy("savings")}>Savings{arrow("savings")}</th>
              <th className="sortable" onClick={() => sortBy("house")}>House{arrow("house")}</th>
              <th className="sortable" onClick={() => sortBy("carry_over")}>Carry Over{arrow("carry_over")}</th>
              <th className="sortable" onClick={() => sortBy("remaining")}>Remaining{arrow("remaining")}</th>
              <th><div className="th-actions">
                  <button className="btn-icon" onClick={toggleMask} title="Hide amounts">
                    {masked ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                  <button className="btn-primary" onClick={() => setEditing("new")}>
                    + Add Fund
                  </button>
                </div></th>
            </tr>
          </thead>
          <tbody>
            {rows.map((f) => {
              const s = sums[f.id];
              return (
                <tr key={f.id}>
                  <td>{f.name}</td>
                  <td><span className="icon-text">{FUND_TYPE_ICONS[f.fund_type]} {FUND_TYPE_LABELS[f.fund_type] ?? f.fund_type}</span></td>
                  <td>{f.cutoff_date ?? "—"}</td>
                  <td>{money(f.amount)}</td>
                  <td>{s ? money(s.expenses) : "—"}</td>
                  <td>{s ? peso(s.savings) : "—"}</td>
                  <td>{s ? peso(s.house) : "—"}</td>
                  <td>{s ? peso(s.carry_over) : "—"}</td>
                  <td style={{ color: s ? remainingColor(s.remaining) : undefined }}>
                    {s ? peso(s.remaining) : "—"}
                  </td>
                  <td className="row-actions">
                    <button onClick={() => navigate(`/transactions?fund=${f.id}`)}>View</button>
                    <button onClick={() => setEditing(f)}>Edit</button>
                    <button
                      className="danger"
                      onClick={() => setDeleteTarget(f)}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {pageCount > 1 && (
        <div className="pager">
          <button disabled={safePage === 0} onClick={() => setPage(safePage - 1)}>
            ‹ Prev
          </button>
          <span>Page {safePage + 1} / {pageCount}</span>
          <button disabled={safePage >= pageCount - 1} onClick={() => setPage(safePage + 1)}>
            Next ›
          </button>
        </div>
      )}

      {editing && (
        <FundModal
          key={editing === "new" ? "new" : editing.id}
          fund={editing === "new" ? null : editing}
          onClose={() => setEditing(null)}
        />
      )}

      {deleteTarget && (
        <Modal
          title="Delete Fund"
          size="sm"
          onClose={() => setDeleteTarget(null)}
          footer={
            <>
              <button onClick={() => setDeleteTarget(null)}>Cancel</button>
              <button
                className="btn-primary"
                style={{ background: "var(--negative)" }}
                onClick={() => {
                  del.mutate(deleteTarget.id, {
                    onSuccess: () => {
                      toast(`Deleted "${deleteTarget.name}"`, "success");
                      setDeleteTarget(null);
                    },
                    onError: () => {
                      toast("Failed to delete fund", "error");
                      setDeleteTarget(null);
                    },
                  });
                }}
                disabled={del.isPending}
              >
                {del.isPending ? "Deleting…" : "Delete"}
              </button>
            </>
          }
        >
          <p>Delete "{deleteTarget.name}" and all its transactions? This cannot be undone.</p>
        </Modal>
      )}
    </div>
  );
}

/** Add (fund=null) or edit (fund set) modal. */
function FundModal({ fund, onClose }: { fund: Fund | null; onClose: () => void }) {
  const create = useCreateFund();
  const update = useUpdateFund();
  const { toast } = useToast();

  const today = new Date().toISOString().slice(0, 10);
  const salaryName = (iso: string) => `${iso.slice(5, 7)}/${iso.slice(8, 10)}/${iso.slice(0, 4)} Salary`;

  const [name, setName] = useState(fund?.name ?? "");
  const [fundType, setFundType] = useState<FundType>((fund?.fund_type as FundType) ?? "salary");
  const [amount, setAmount] = useState(fund ? String(fund.amount) : "");
  const [cutoff, setCutoff] = useState(fund?.cutoff_date ?? today);
  const [notes, setNotes] = useState(fund?.notes ?? "");

  // Salary funds are always named "MM/DD/YYYY Salary" (no other scheme, locked).
  const isSalary = fundType === "salary";
  const effectiveName = isSalary ? salaryName(cutoff) : name;

  const save = () => {
    const payload = {
      name: effectiveName.trim(),
      fund_type: fundType,
      amount: parseFloat(amount) || 0,
      cutoff_date: cutoff || null,
      notes: notes || null,
    };
    const done = {
      onSuccess: () => {
        toast(fund ? `Updated "${effectiveName.trim()}"` : `Created "${effectiveName.trim()}"`, "success");
        onClose();
      },
      onError: () => toast("Failed to save fund", "error"),
    };
    if (fund) update.mutate({ id: fund.id, ...payload }, done);
    else create.mutate(payload, done);
  };

  const pending = create.isPending || update.isPending;

  return (
    <Modal
      title={fund ? "Edit Fund" : "Add Fund"}
      onClose={onClose}
      footer={
        <>
          <button onClick={onClose}>Cancel</button>
          <button className="btn-primary" disabled={!effectiveName.trim() || pending} onClick={save}>
            {pending ? "Saving…" : "Save"}
          </button>
        </>
      }
    >
      <label>
        Name {isSalary && <span className="icon-text" style={{ color: "var(--text-muted)", fontSize: 11 }}><Lock size={11} /> auto from cutoff date</span>}
        {isSalary ? (
          <input value={effectiveName} readOnly title="Salary funds are named automatically from the cutoff date" />
        ) : (
          <input value={name} onChange={(e) => setName(e.target.value)} />
        )}
      </label>
      <label>
        Type
        <select value={fundType} onChange={(e) => setFundType(e.target.value as FundType)}>
          <option value="salary">Salary</option>
          <option value="bonus">Bonus</option>
          <option value="espp">ESPP</option>
          <option value="other">Other</option>
        </select>
      </label>
      <label>
        Income amount
        <input type="number" step="0.01" value={amount} onChange={(e) => setAmount(e.target.value)} />
      </label>
      <label>
        Cutoff date
        <input type="date" value={cutoff ?? ""} onChange={(e) => setCutoff(e.target.value)} />
      </label>
      <label>
        Notes
        <input value={notes ?? ""} onChange={(e) => setNotes(e.target.value)} />
      </label>
    </Modal>
  );
}
