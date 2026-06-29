import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import {
  useTransactions,
  useCreateTransaction,
  useUpdateTransaction,
  useDeleteTransaction,
} from "../hooks/useTransactions";
import { useFunds, useFundSummaries } from "../hooks/useFunds";
import { useCategories } from "../hooks/useCategories";
import { peso } from "../components/StatCard";
import { remainingColor } from "../theme";
import Modal from "../components/Modal";
import type { Transaction } from "../api/types";

const PAGE_SIZE = 20;
type SortCol = "txn_date" | "category" | "amount" | "remarks";

/** Transactions — one fund at a time (left nav panel) + add / edit / delete. */
export default function Transactions() {
  const funds = useFunds();
  const summaries = useFundSummaries();
  const [params] = useSearchParams();
  const [fundId, setFundId] = useState<number | null>(null);
  const [navSearch, setNavSearch] = useState("");
  const [rowSearch, setRowSearch] = useState("");
  const [page, setPage] = useState(0);
  const [editing, setEditing] = useState<Transaction | "new" | null>(null);
  const [masked, setMasked] = useState(() => localStorage.getItem("mask") === "1");
  const [sortCol, setSortCol] = useState<SortCol>("txn_date");
  const [sortAsc, setSortAsc] = useState(true);

  const toggleMask = () => {
    setMasked((m) => { localStorage.setItem("mask", m ? "0" : "1"); return !m; });
  };
  const money = (v: number) => (masked ? "₱ ••••" : peso(v));

  // Default to the ?fund= param or the first fund once loaded (no "All" view).
  useEffect(() => {
    if (fundId === null && funds.data && funds.data.length > 0) {
      const q = Number(params.get("fund"));
      setFundId(q && funds.data.some((f) => f.id === q) ? q : funds.data[0].id);
    }
  }, [funds.data, fundId, params]);

  const txns = useTransactions(fundId ?? undefined);
  const del = useDeleteTransaction();

  const navFunds = useMemo(() => {
    const q = navSearch.trim().toLowerCase();
    const list = funds.data ?? [];
    return q ? list.filter((f) => f.name.toLowerCase().includes(q)) : list;
  }, [funds.data, navSearch]);

  const rowsSorted = useMemo(() => {
    let list = txns.data ?? [];
    const q = rowSearch.trim().toLowerCase();
    if (q) list = list.filter((t) =>
      t.category.toLowerCase().includes(q) || (t.remarks ?? "").toLowerCase().includes(q));
    const key = (t: Transaction): number | string => {
      switch (sortCol) {
        case "category": return t.category.toLowerCase();
        case "amount": return t.amount;
        case "remarks": return (t.remarks ?? "").toLowerCase();
        default: return t.txn_date ?? "";
      }
    };
    return [...list].sort((a, b) => {
      const ka = key(a), kb = key(b);
      const cmp = ka < kb ? -1 : ka > kb ? 1 : 0;
      return sortAsc ? cmp : -cmp;
    });
  }, [txns.data, rowSearch, sortCol, sortAsc]);

  if (funds.isLoading) return <p>Loading…</p>;
  if (funds.isError || !funds.data) return <p>Could not load funds.</p>;

  const pageCount = Math.ceil(rowsSorted.length / PAGE_SIZE);
  const safePage = Math.min(page, Math.max(0, pageCount - 1));
  const rows = rowsSorted.slice(safePage * PAGE_SIZE, safePage * PAGE_SIZE + PAGE_SIZE);
  const activeFund = funds.data.find((f) => f.id === fundId);
  const sum = fundId ? summaries.data?.[fundId] : undefined;
  const sortBy = (c: SortCol) => c === sortCol ? setSortAsc((a) => !a) : (setSortCol(c), setSortAsc(true));
  const arrow = (c: SortCol) => (sortCol === c ? (sortAsc ? " ▲" : " ▼") : "");

  return (
    <div className="txn-layout">
      <aside className="fund-nav">
        <h3>📂 Income Funds</h3>
        <input
          className="cat-search"
          placeholder="Search fund…"
          value={navSearch}
          onChange={(e) => setNavSearch(e.target.value)}
        />
        <div className="fund-nav-list">
          {navFunds.map((f) => (
            <button
              key={f.id}
              className={f.id === fundId ? "fund-nav-item active" : "fund-nav-item"}
              onClick={() => { setFundId(f.id); setPage(0); }}
            >
              {f.name}
            </button>
          ))}
        </div>
      </aside>

      <section className="txn-main">
        <div className="page-head">
          <h2 className="page-title">{activeFund?.name ?? "Transactions"}</h2>
          <div className="head-actions">
            <button className="btn-icon" onClick={toggleMask} title="Hide amounts">
              {masked ? "🙈" : "👁"}
            </button>
            <button className="btn-primary" disabled={!fundId} onClick={() => setEditing("new")}>
              + Add
            </button>
          </div>
        </div>

        {/* Per-fund summary cards — only Income + Expenses are masked, like desktop */}
        {sum && (
          <div className="mini-cards">
            <div className="mini-card"><span>Income</span><b>{money(sum.income)}</b></div>
            <div className="mini-card"><span>Expenses</span><b>{money(sum.expenses)}</b></div>
            <div className="mini-card"><span>Savings</span>
              <b>{peso(activeFund?.fund_type === "other" ? sum.house + sum.remaining : sum.savings)}</b>
            </div>
            <div className="mini-card"><span>House</span><b>{peso(sum.house)}</b></div>
            <div className="mini-card"><span>Carry Over</span><b>{peso(sum.carry_over)}</b></div>
            <div className="mini-card"><span>Remaining</span>
              <b style={{ color: remainingColor(sum.remaining) }}>{peso(sum.remaining)}</b>
            </div>
          </div>
        )}

        <input
          className="cat-search"
          placeholder="🔍 Search category or remarks…"
          value={rowSearch}
          onChange={(e) => { setRowSearch(e.target.value); setPage(0); }}
        />

        {txns.isLoading ? (
          <p>Loading…</p>
        ) : (
          <>
            <table>
              <thead>
                <tr>
                  <th className="sortable" onClick={() => sortBy("txn_date")}>Date{arrow("txn_date")}</th>
                  <th className="sortable" onClick={() => sortBy("category")}>Category{arrow("category")}</th>
                  <th className="sortable" onClick={() => sortBy("amount")}>Amount{arrow("amount")}</th>
                  <th className="sortable" onClick={() => sortBy("remarks")}>Remarks{arrow("remarks")}</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {rows.map((t) => (
                  <tr key={t.id}>
                    <td>{t.txn_date ?? "—"}</td>
                    <td>{t.category}</td>
                    <td className={t.amount < 0 ? "negative" : "positive"}>
                      {peso(t.amount)}
                    </td>
                    <td>{t.remarks ?? ""}</td>
                    <td className="row-actions">
                      <button onClick={() => setEditing(t)}>Edit</button>
                      <button
                        className="danger"
                        onClick={() => {
                          if (confirm("Delete this transaction?")) del.mutate(t.id);
                        }}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
                {rows.length === 0 && (
                  <tr><td colSpan={5} className="settings-empty">No transactions.</td></tr>
                )}
              </tbody>
            </table>

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
          </>
        )}
      </section>

      {editing && fundId && (
        <TxnModal
          key={editing === "new" ? "new" : editing.id}
          fundId={fundId}
          txn={editing === "new" ? null : editing}
          onClose={() => setEditing(null)}
        />
      )}
    </div>
  );
}

/** Add (txn=null) or edit (txn set) modal. Fund is fixed to the active panel. */
function TxnModal({
  fundId,
  txn,
  onClose,
}: {
  fundId: number;
  txn: Transaction | null;
  onClose: () => void;
}) {
  const cats = useCategories();
  const create = useCreateTransaction();
  const update = useUpdateTransaction();

  const [category, setCategory] = useState(txn?.category ?? "");
  const [amount, setAmount] = useState(txn ? String(txn.amount) : "");
  const [date, setDate] = useState(txn?.txn_date ?? new Date().toISOString().slice(0, 10));
  const [remarks, setRemarks] = useState(txn?.remarks ?? "");

  const save = () => {
    const payload = {
      category,
      amount: parseFloat(amount) || 0,
      txn_date: date || null,
      remarks: remarks || null,
    };
    const done = { onSuccess: onClose };
    if (txn) update.mutate({ id: txn.id, ...payload }, done);
    else create.mutate({ fund_id: fundId, ...payload }, done);
  };

  const pending = create.isPending || update.isPending;
  const valid = category.trim() !== "" && amount !== "";

  return (
    <Modal
      title={txn ? "Edit Transaction" : "Add Transaction"}
      onClose={onClose}
      footer={
        <>
          <button onClick={onClose}>Cancel</button>
          <button className="btn-primary" disabled={!valid || pending} onClick={save}>
            {pending ? "Saving…" : "Save"}
          </button>
        </>
      }
    >
      <label>
        Category
        <input
          list="cat-list"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
        />
        <datalist id="cat-list">
          {(cats.data ?? []).map((c) => (
            <option key={c} value={c} />
          ))}
        </datalist>
      </label>
      <label>
        Amount
        <input type="number" step="0.01" value={amount} onChange={(e) => setAmount(e.target.value)} />
      </label>
      <label>
        Date
        <input type="date" value={date ?? ""} onChange={(e) => setDate(e.target.value)} />
      </label>
      <label>
        Remarks
        <input value={remarks ?? ""} onChange={(e) => setRemarks(e.target.value)} />
      </label>
    </Modal>
  );
}
