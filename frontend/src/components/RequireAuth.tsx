import { Navigate } from "react-router-dom";
import { isAuthenticated } from "../hooks/useAuth";

/** Gate protected routes — redirect to /login when no JWT is stored. */
export default function RequireAuth({ children }: { children: JSX.Element }) {
  return isAuthenticated() ? children : <Navigate to="/login" replace />;
}
