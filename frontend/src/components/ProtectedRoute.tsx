import { Navigate } from "react-router-dom";

import { useAuth } from "../auth";

export function ProtectedRoute({
  roles,
  children
}: {
  roles: Array<"viewer" | "analyst" | "admin">;
  children: React.ReactElement;
}) {
  const { user } = useAuth();
  if (!roles.includes(user.role)) {
    return <Navigate replace to="/" />;
  }
  return children;
}
