import { useMemo, useState } from "react";
import Spinner from "../components/Spinner";
import Modal from "../components/Modal";
import { useToast } from "../components/Toast";
import {
  useCurrentUser,
  useRegister,
  useUsers,
  useDeleteUser,
  useDeactivateUser,
  useActivateUser,
  useResetPassword,
  type UserInfo,
} from "../hooks/useAuth";
import { Users, KeyRound, UserPlus, PauseCircle, PlayCircle, Trash2 } from "lucide-react";

function ConfirmModal({
  title,
  message,
  confirmLabel,
  danger,
  loading,
  onConfirm,
  onClose,
}: {
  title: string;
  message: string;
  confirmLabel: string;
  danger?: boolean;
  loading: boolean;
  onConfirm: () => void;
  onClose: () => void;
}) {
  return (
    <Modal
      title={title}
      onClose={onClose}
      footer={
        <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
          <button className="btn-primary" onClick={onClose} disabled={loading}>
            Cancel
          </button>
          <button
            className={`btn-primary${danger ? " danger" : ""}`}
            onClick={onConfirm}
            disabled={loading}
            style={
              danger
                ? { background: "var(--negative)", color: "#fff" }
                : undefined
            }
          >
            {loading ? "Processing…" : confirmLabel}
          </button>
        </div>
      }
    >
      <p>{message}</p>
    </Modal>
  );
}

function PasswordModal({
  user,
  onClose,
}: {
  user: UserInfo;
  onClose: () => void;
}) {
  const reset = useResetPassword();
  const { toast } = useToast();
  const [pw, setPw] = useState("");

  const submit = () => {
    if (!pw) return;
    reset.mutate(
      { userId: user.id, password: pw },
      {
        onSuccess: () => {
          toast(`Password updated for "${user.username}"`, "success");
          onClose();
        },
        onError: (err: any) => {
          toast(err?.response?.data?.detail ?? "Error updating password", "error");
        },
      },
    );
  };

  return (
      <Modal
      title={<span className="icon-text"><KeyRound size={16} /> Set Password — {user.username}</span>}
      onClose={onClose}
      footer={
        <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
          <button className="btn-primary" onClick={onClose} disabled={reset.isPending}>
            Cancel
          </button>
          <button
            className="btn-primary"
            onClick={submit}
            disabled={reset.isPending || !pw}
          >
            {reset.isPending ? "Saving…" : "Set Password"}
          </button>
        </div>
      }
    >
      <label>
        New password
        <input
          type="password"
          value={pw}
          onChange={(e) => setPw(e.target.value)}
          autoFocus
        />
      </label>
    </Modal>
  );
}

function NewUserForm({ onCreated }: { onCreated: () => void }) {
  const reg = useRegister();
  const { toast } = useToast();
  const [u, setU] = useState("");
  const [p, setP] = useState("");

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const uname = u.trim();
    if (!uname || !p) return;
    reg.mutate(
      { username: uname, password: p },
      {
        onSuccess: () => {
          setU("");
          setP("");
          toast(`Created "${uname}"`, "success");
          onCreated();
        },
        onError: (err: any) => {
          const detail = err?.response?.data?.detail ?? "Error";
          toast(detail, "error");
        },
      },
    );
  };

  return (
    <section className="settings-card" style={{ marginBottom: 20 }}>
      <h3><span className="icon-text"><UserPlus size={16} /> Create Account</span></h3>
      <form className="inline-form" onSubmit={submit}>
        <input
          placeholder="Username"
          value={u}
          onChange={(e) => setU(e.target.value)}
        />
        <input
          type="password"
          placeholder="Password"
          value={p}
          onChange={(e) => setP(e.target.value)}
        />
        <button type="submit" disabled={reg.isPending || !u.trim() || !p}>
          {reg.isPending ? "Creating…" : "Create"}
        </button>
      </form>
    </section>
  );
}

export default function Accounts() {
  const { data: users, isLoading } = useUsers();
  const currentUser = useCurrentUser();
  const deleteUser = useDeleteUser();
  const deactivateUser = useDeactivateUser();
  const activateUser = useActivateUser();
  const { toast } = useToast();
  const [sortCol, setSortCol] = useState("id");
  const [sortAsc, setSortAsc] = useState(true);

  const [confirm, setConfirm] = useState<{
    type: "delete" | "deactivate" | "activate";
    user: UserInfo;
  } | null>(null);

  const [passwordTarget, setPasswordTarget] = useState<UserInfo | null>(null);

  const handleConfirm = () => {
    if (!confirm) return;
    const u = confirm.user;
    const onSettled = () => {
      setConfirm(null);
      if (confirm.type === "delete") toast(`Deleted "${u.username}"`, "success");
      else if (confirm.type === "deactivate") toast(`Deactivated "${u.username}"`, "info");
      else toast(`Activated "${u.username}"`, "success");
    };
    if (confirm.type === "delete")
      deleteUser.mutate(u.id, { onSettled });
    else if (confirm.type === "deactivate")
      deactivateUser.mutate(u.id, { onSettled });
    else activateUser.mutate(u.id, { onSettled });
  };

  const isProcessing =
    deleteUser.isPending || deactivateUser.isPending || activateUser.isPending;

  const sorted = useMemo(() => {
    if (!users) return [];
    return [...users].sort((a, b) => {
      const ka = sortCol === "id" || sortCol === "is_active" ? (a[sortCol] ? 1 : 0) : (a[sortCol as "username" | "created_at"] ?? "").toString().toLowerCase();
      const kb = sortCol === "id" || sortCol === "is_active" ? (b[sortCol] ? 1 : 0) : (b[sortCol as "username" | "created_at"] ?? "").toString().toLowerCase();
      const cmp = ka < kb ? -1 : ka > kb ? 1 : 0;
      return sortAsc ? cmp : -cmp;
    });
  }, [users, sortCol, sortAsc]);
  const sortBy = (col: string) => col === sortCol ? setSortAsc((a) => !a) : (setSortCol(col), setSortAsc(col !== "is_active"));
  const arrow = (col: string) => (sortCol === col ? (sortAsc ? " ▲" : " ▼") : "");

  return (
    <div>
      <div className="page-head">
        <h2 className="page-title"><span className="icon-text"><Users size={20} /> Accounts</span></h2>
      </div>

      <NewUserForm onCreated={() => {}} />

      {isLoading && <Spinner />}

      {users && users.length > 0 && (
        <div className="table-wrap">
          <table className="account-table">
            <thead>
              <tr>
                <th className="sortable" onClick={() => sortBy("id")}>ID{arrow("id")}</th>
                <th className="sortable" onClick={() => sortBy("username")}>Username{arrow("username")}</th>
                <th className="sortable" onClick={() => sortBy("created_at")}>Created{arrow("created_at")}</th>
                <th className="sortable" onClick={() => sortBy("is_active")}>Status{arrow("is_active")}</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
            {sorted.map((u) => {
              const isMe = currentUser?.id === u.id;
              return (
                <tr key={u.id}>
                  <td>{u.id}</td>
                  <td>
                    {u.username}
                    {isMe ? " (you)" : ""}
                  </td>
                  <td>
                    {u.created_at
                      ? new Date(u.created_at).toLocaleDateString()
                      : "—"}
                  </td>
                  <td>
                    <span
                      className={`status-badge ${u.is_active ? "active" : "inactive"}`}
                    >
                      {u.is_active ? "Active" : "Inactive"}
                    </span>
                  </td>
                  <td>
                    <div className="row-actions">
                      <button
                        className="btn-icon"
                        title="Set Password"
                        onClick={() => setPasswordTarget(u)}
                      >
                        <KeyRound size={16} />
                      </button>
                      {u.is_active ? (
                        <button
                          className="btn-icon"
                          disabled={isMe}
                          title="Deactivate"
                          onClick={() =>
                            setConfirm({ type: "deactivate", user: u })
                          }
                        >
                          <span className="icon-text"><PauseCircle size={14} /> Deactivate</span>
                        </button>
                      ) : (
                        <button
                          className="btn-icon"
                          title="Activate"
                          onClick={() =>
                            setConfirm({ type: "activate", user: u })
                          }
                        >
                          <span className="icon-text"><PlayCircle size={14} /> Activate</span>
                        </button>
                      )}
                      <button
                        className="btn-icon danger"
                        disabled={isMe}
                        title="Delete"
                        onClick={() =>
                          setConfirm({ type: "delete", user: u })
                        }
                      >
                        <span className="icon-text"><Trash2 size={14} /> Delete</span>
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      )}

      {confirm && (
        <ConfirmModal
          title={
            confirm.type === "delete"
              ? "Delete Account"
              : confirm.type === "deactivate"
                ? "Deactivate Account"
                : "Activate Account"
          }
          message={
            confirm.type === "delete"
              ? `Permanently delete "${confirm.user.username}" and ALL their data? This cannot be undone.`
              : confirm.type === "deactivate"
                ? `Deactivate "${confirm.user.username}"? They won't be able to log in until reactivated.`
                : `Reactivate "${confirm.user.username}"?`
          }
          confirmLabel={
            confirm.type === "delete"
              ? "Delete"
              : confirm.type === "deactivate"
                ? "Deactivate"
                : "Activate"
          }
          danger={confirm.type === "delete"}
          loading={isProcessing}
          onConfirm={handleConfirm}
          onClose={() => setConfirm(null)}
        />
      )}

      {passwordTarget && (
        <PasswordModal
          user={passwordTarget}
          onClose={() => setPasswordTarget(null)}
        />
      )}
    </div>
  );
}
