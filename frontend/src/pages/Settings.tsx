import { useMemo, useState } from "react";
import { useCategories, useAddCategory } from "../hooks/useCategories";
import { useBpiBalance, useSetBpiBalance } from "../hooks/useBpi";
import { peso } from "../components/StatCard";
import { useToast } from "../components/Toast";
import Modal from "../components/Modal";
import { Settings as SettingsIcon, CreditCard, Info, Tags, Pencil, Plus } from "lucide-react";

/** Settings — BPI balance, expense categories + about. */
export default function Settings() {
  return (
    <div>
      <div className="page-head">
        <h2 className="page-title"><span className="icon-text"><SettingsIcon size={20} /> Settings</span></h2>
      </div>
      <BpiCategoriesPanel />
      <AboutPanel />
    </div>
  );
}

/** Combined hero card — BPI balance (centered) + expense categories with inline expand. */
function BpiCategoriesPanel() {
  const bpi = useBpiBalance();
  const save = useSetBpiBalance();
  const cats = useCategories();
  const add = useAddCategory();
  const { toast } = useToast();

  const [showBpiModal, setShowBpiModal] = useState(false);
  const [draft, setDraft] = useState("");
  const [search, setSearch] = useState("");
  const [showAddModal, setShowAddModal] = useState(false);
  const [name, setName] = useState("");
  const [showAll, setShowAll] = useState(false);

  const allCats = cats.data ?? [];
  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return q ? allCats.filter((c) => c.toLowerCase().includes(q)) : allCats;
  }, [allCats, search]);
  const visible = showAll ? filtered : filtered.slice(0, 20);
  const hasMore = filtered.length > 20;

  const submitBpi = () => {
    const n = parseFloat(draft.replace(/,/g, ""));
    if (Number.isNaN(n)) { toast("Invalid number", "error"); return; }
    save.mutate(n, {
      onSuccess: () => { setDraft(""); setShowBpiModal(false); toast("Balance updated", "success"); },
    });
  };

  const submitCat = () => {
    const v = name.trim();
    if (v) add.mutate(v, { onSuccess: () => { setName(""); setShowAddModal(false); } });
  };

  const recorded = bpi.data?.recorded_at
    ? new Date(bpi.data.recorded_at).toLocaleString()
    : null;

  return (
    <section className="bpi-hero">
      <div className="bpi-strip" />

      {/* ── BPI section (centered) ── */}
      <div className="bpi-body bpi-cats-top">
        <h3 className="bpi-cats-center"><span className="icon-text"><CreditCard size={16} /> BPI Current Balance</span></h3>
        <div className="bpi-amount-row bpi-cats-center">
          <div className="bpi-amount">{bpi.data ? peso(bpi.data.balance) : "…"}</div>
          <button className="btn-icon" onClick={() => { setDraft(""); setShowBpiModal(true); }} title="Update balance">
            <Pencil size={15} />
          </button>
        </div>
        {recorded && <p className="bpi-recorded bpi-cats-center">Last updated {recorded}</p>}
      </div>

      <hr className="bpi-divider" />

      {/* ── Categories section ── */}
      <div className="bpi-body">
        <h3>
          <span className="icon-text"><Tags size={16} /> Expense Categories ({allCats.length})</span>
          <button className="btn-icon" onClick={() => { setName(""); setShowAddModal(true); }} title="Add category">
            <Plus size={15} />
          </button>
        </h3>
        <input className="cat-search" placeholder="Search…" value={search} onChange={(e) => setSearch(e.target.value)} />
        <div className="chip-wrap">
          {visible.map((c) => <span className="chip" key={c}>{c}</span>)}
          {visible.length === 0 && <span className="settings-empty">No categories.</span>}
        </div>
        {hasMore && (
          <button className="see-all" onClick={() => setShowAll((a) => !a)}>
            {showAll ? "Show less ↑" : `See all (${filtered.length}) →`}
          </button>
        )}
      </div>

      {/* ── BPI edit modal ── */}
      {showBpiModal && (
        <Modal title="Update BPI Balance" onClose={() => setShowBpiModal(false)} size="sm"
          footer={
            <button className="btn-primary" onClick={submitBpi} disabled={save.isPending || draft === ""}>
              {save.isPending ? "Saving…" : "Save"}
            </button>
          }>
          <label>
            New balance
            <input type="number" step="0.01" placeholder="0.00" value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && submitBpi()} />
          </label>
          <div className="modal-notice">Enter the balance shown in your BPI account overview. Used for net worth calculations.</div>
        </Modal>
      )}

      {/* ── Add category modal ── */}
      {showAddModal && (
        <Modal title="Add Category" onClose={() => setShowAddModal(false)} size="sm"
          footer={
            <button className="btn-primary" onClick={submitCat} disabled={add.isPending || name.trim() === ""}>
              {add.isPending ? "Adding…" : "Add"}
            </button>
          }>
          <label>
            Category name
            <input placeholder="e.g. Groceries" value={name}
              onChange={(e) => setName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && submitCat()} />
          </label>
          <div className="modal-notice">New categories appear in transaction dropdowns and reports.</div>
        </Modal>
      )}

    </section>
  );
}

/** Static app info. */
function AboutPanel() {
  return (
    <section className="settings-card">
      <h3><span className="icon-text"><Info size={16} /> About</span></h3>
      <ul className="kv-list">
        <li><span>App</span><strong>Budget Tracker</strong></li>
        <li><span>Version</span><strong>1.0 — Web</strong></li>
        <li><span>Theme</span><strong>Dark</strong></li>
        <li><span>Currency</span><strong>PHP (₱)</strong></li>
      </ul>
    </section>
  );
}
