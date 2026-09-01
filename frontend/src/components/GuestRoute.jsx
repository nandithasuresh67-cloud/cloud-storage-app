import { Navigate } from "react-router-dom";
import { useMe } from "../hooks/useAuth";

export default function GuestRoute({ children }) {
  const { data: user, isLoading } = useMe();

  if (isLoading) return null; // avoid a flash of the login form before the /auth/me check resolves

  if (user) {
    return <Navigate to="/" replace />;
  }

  return children;
}
