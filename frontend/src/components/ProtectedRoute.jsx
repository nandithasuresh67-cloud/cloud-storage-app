import { Navigate } from "react-router-dom";
import { Loader2 } from "lucide-react";
import { useMe } from "../hooks/useAuth";

export default function ProtectedRoute({ children }) {
  const { data: user, isLoading, isError } = useMe();

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-stone-50">
        <Loader2 className="h-6 w-6 animate-spin text-stone-400" />
      </div>
    );
  }

  if (isError || !user) {
    return <Navigate to="/login" replace />;
  }

  return children;
}
