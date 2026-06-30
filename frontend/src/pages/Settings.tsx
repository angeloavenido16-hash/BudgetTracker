import { useMemo, useState } from "react";
import { useCategories, useAddCategory } from "../hooks/useCategories";
import { useBpiBalance, useSetBpiBalance } from "../hooks/useBpi";
import { peso } from "../components/StatCard";
import { useToast } from "../components/Toast";
import { Settings as SettingsIcon, CreditCard, Info, Tags, Save } from "lucide-react";

/** Settings — BPI balance, expense categories + about. */
export default function Settings() {
  return (
    <div>
      <div className="page-head">
        <h2 className="page-title"><span className="icon-text"><SettingsIcon size={20} /> Settings</span></h2>
      </div>
      <BpiPanel />
      <CategoryPanel />
      <AboutPanel />
    </div>
  );
}

/** Latest bank balance — hero card with accent strip + inline editor. */
function BpiPanel() {
  const bpi = useBpiBalance();
  const save = useSetBpiBalance();
  const { toast } = useToast();
  const [draft, setDraft] = useState("");

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const n = parseFloat(draft.replace(/,/g, ""));
    if (Number.isNaN(n)) { toast("Invalid number", "error"); return; }
    save.mutate(n, {
      onSuccess: () => {
        setDraft("");
        toast("Balance updated", "success");
      },
    });
  };

  const recorded = bpi.data?.recorded_at
    ? new Date(bpi.data.recorded_at).toLocaleString()
    : null;

  return (
    <section className="bpi-hero">
      <div className="bpi-strip" />
      <div className="bpi-body">
        <h3><span className="icon-text"><CreditCard size={16} /> BPI Current Balance</span></h3>
        <div className="bpi-amount">{bpi.data ? peso(bpi.data.balance) : "…"}</div>
        {recorded && <p className="bpi-recorded">Last updated {recorded}</p>}
        <form className="inline-form" onSubmit={submit}>
          <input
            type="number"
            step="0.01"
            placeholder="New balance"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
          />
          <button type="submit" disabled={save.isPending || draft === ""}>
            <span className="icon-text"><Save size={14} /> {save.isPending ? "Saving…" : "Update Balance"}</span>
          </button>
        </form>
      </div>
    </section>
  );
}

/** Static app info. */
function AboutPanel() {
  return (
    <section className="settings-card cat-card">
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


/** Searchable list of expense categories with add. */
function CategoryPanel() {
  const cats = useCategories();
  const add = useAddCategory();
  const [search, setSearch] = useState("");
  const [name, setName] = useState("");

  const filtered = useMemo(() => {
    const list = cats.data ?? [];
    const q = search.trim().toLowerCase();
    return q ? list.filter((c) => c.toLowerCase().includes(q)) : list;
  }, [cats.data, search]);

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const v = name.trim();
    if (v) add.mutate(v, { onSuccess: () => setName("") });
  };

  return (
    <section className="settings-card cat-card">
      <h3><span className="icon-text"><Tags size={16} /> Expense Categories ({cats.data?.length ?? 0})</span></h3>
      <form className="inline-form" onSubmit={submit}>
        <input
          placeholder="New category"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <button type="submit" disabled={add.isPending || name.trim() === ""}>
          Add
        </button>
      </form>
      <input
        className="cat-search"
        placeholder="Search…"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />
      <div className="chip-wrap">
        {filtered.map((c) => (
          <span className="chip" key={c}>
            {c}
          </span>
        ))}
        {filtered.length === 0 && (
          <span className="settings-empty">No categories.</span>
        )}
      </div>
    </section>
  );
}
