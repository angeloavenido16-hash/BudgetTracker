import { NavLink } from "react-router-dom";
import { logout, useCurrentUser } from "../hooks/useAuth";
import { useState } from "react";
import { X } from "lucide-react";

const COMMON = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/funds", label: "Income Funds" },
  { to: "/transactions", label: "Transactions" },
  { to: "/reports", label: "Reports" },
  { to: "/settings", label: "Settings" },
];

export default function Sidebar() {
  const user = useCurrentUser();
  const [open, setOpen] = useState(false);
  const nav = user?.is_admin
    ? [...COMMON, { to: "/accounts", label: "Accounts" }]
    : COMMON;

  const close = () => setOpen(false);

  return (
    <>
      {!open && (
        <button className="hamburger" onClick={() => setOpen(true)} aria-label="Open menu">
          ☰
        </button>
      )}
      <div className={`sidebar-overlay${open ? " open" : ""}`} onClick={close} />
      <nav className={`sidebar${open ? " open" : ""}`}>
        <div className="sidebar-head">
          <h1>Budget Tracker</h1>
          <button className="sidebar-close" onClick={close} aria-label="Close menu">
            <X size={18} />
          </button>
        </div>
        {nav.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => (isActive ? "active" : "")}
            onClick={close}
          >
            {item.label}
          </NavLink>
        ))}
        <button className="sidebar-logout" onClick={logout}>
          Sign out
        </button>
      </nav>
    </>
  );
}
