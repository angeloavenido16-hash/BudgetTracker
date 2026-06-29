import { NavLink } from "react-router-dom";
import { logout, useCurrentUser } from "../hooks/useAuth";

const COMMON = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/funds", label: "Income Funds" },
  { to: "/transactions", label: "Transactions" },
  { to: "/reports", label: "Reports" },
  { to: "/settings", label: "Settings" },
];

/** Persistent left navigation — mirrors the desktop sidebar. */
export default function Sidebar() {
  const user = useCurrentUser();
  const nav = user?.is_admin
    ? [...COMMON, { to: "/accounts", label: "Accounts" }]
    : COMMON;

  return (
    <nav className="sidebar">
      <h1>Budget Tracker</h1>
      {nav.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          className={({ isActive }) => (isActive ? "active" : "")}
        >
          {item.label}
        </NavLink>
      ))}
      <button className="sidebar-logout" onClick={logout}>
        Sign out
      </button>
    </nav>
  );
}
