import { Routes, Route, Navigate } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import RequireAuth from "./components/RequireAuth";
import { ToastProvider } from "./components/Toast";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Funds from "./pages/Funds";
import Transactions from "./pages/Transactions";
import Reports from "./pages/Reports";
import Settings from "./pages/Settings";
import Accounts from "./pages/Accounts";

/** Authenticated shell: persistent sidebar + routed main content. */
function Shell() {
  return (
    <div className="app-shell">
      <Sidebar />
      <main className="app-main">
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/funds" element={<Funds />} />
          <Route path="/transactions" element={<Transactions />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/accounts" element={<Accounts />} />
        </Routes>
      </main>
    </div>
  );
}

/**
 * Top-level routing: /login is public, everything else is gated behind a JWT.
 * Mirrors the desktop app's 5 views (Dashboard, Funds, Transactions, Reports, Settings).
 */
export default function App() {
  return (
    <ToastProvider>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/*"
          element={
            <RequireAuth>
              <Shell />
            </RequireAuth>
          }
        />
      </Routes>
    </ToastProvider>
  );
}
