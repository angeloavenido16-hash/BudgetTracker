import { NavLink } from "react-router-dom";
import { logout } from "../hooks/useAuth";

const NAV = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/funds", label: "Income Funds" },
  { to: "/transactions", label: "Transactions" },
  { to: "/reports", label: "Reports" },
  { to: "/settings", label: "Settings" },
];

/** Persistent left navigation — mirrors the desktop sidebar. */
export default function Sidebar() {
  return (
    <nav className="sidebar">
      <h1>Budget Tracker</h1>
      {NAV.map((item) => (
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
