import { useState } from "react";
import Modal from "../components/Modal";
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
  const [pw, setPw] = useState("");
  const [msg, setMsg] = useState("");

  const submit = () => {
    if (!pw) return;
    reset.mutate(
      { userId: user.id, password: pw },
      {
        onSuccess: () => {
          setMsg(`✅ Password updated for "${user.username}"`);
          setTimeout(onClose, 1500);
        },
        onError: (err: any) => {
          setMsg(`❌ ${err?.response?.data?.detail ?? "Error"}`);
        },
      },
    );
  };

  return (
    <Modal
      title={`🔑 Set Password — ${user.username}`}
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
      {msg && (
        <p style={{ margin: 0, fontSize: 13, fontWeight: 600 }}>
          {msg}
        </p>
      )}
    </Modal>
  );
}

function NewUserForm({ onCreated }: { onCreated: () => void }) {
  const reg = useRegister();
  const [u, setU] = useState("");
  const [p, setP] = useState("");
  const [msg, setMsg] = useState("");

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
          setMsg(`✅ Created "${uname}"`);
          onCreated();
          setTimeout(() => setMsg(""), 3000);
        },
        onError: (err: any) => {
          const detail = err?.response?.data?.detail ?? "Error";
          setMsg(`❌ ${detail}`);
          setTimeout(() => setMsg(""), 5000);
        },
      },
    );
  };

  return (
    <section className="settings-card" style={{ marginBottom: 20 }}>
      <h3>👤 Create Account</h3>
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
        {msg && (
          <span style={{ color: "var(--positive)", fontWeight: 600 }}>
            {msg}
          </span>
        )}
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

  const [confirm, setConfirm] = useState<{
    type: "delete" | "deactivate" | "activate";
    user: UserInfo;
  } | null>(null);

  const [passwordTarget, setPasswordTarget] = useState<UserInfo | null>(null);

  const handleConfirm = () => {
    if (!confirm) return;
    const u = confirm.user;
    if (confirm.type === "delete")
      deleteUser.mutate(u.id, { onSettled: () => setConfirm(null) });
    else if (confirm.type === "deactivate")
      deactivateUser.mutate(u.id, { onSettled: () => setConfirm(null) });
    else activateUser.mutate(u.id, { onSettled: () => setConfirm(null) });
  };

  const isProcessing =
    deleteUser.isPending || deactivateUser.isPending || activateUser.isPending;

  return (
    <div>
      <h2 className="page-title">👥 Accounts</h2>

      <NewUserForm onCreated={() => {}} />

      {isLoading && <p>Loading…</p>}

      {users && users.length > 0 && (
        <table className="account-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Username</th>
              <th>Created</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => {
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
                        🔑
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
                          ⏸ Deactivate
                        </button>
                      ) : (
                        <button
                          className="btn-icon"
                          title="Activate"
                          onClick={() =>
                            setConfirm({ type: "activate", user: u })
                          }
                        >
                          ▶ Activate
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
                        🗑 Delete
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
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
