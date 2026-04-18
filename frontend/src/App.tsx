import { Navigate, Route, Routes } from "react-router-dom";

import { ProtectedRoute } from "./components/ProtectedRoute";
import { GraphExplorer } from "./pages/GraphExplorer";
import { BusinessProfile } from "./pages/BusinessProfile";
import { Dashboard } from "./pages/Dashboard";
import { PincodeExplorer } from "./pages/PincodeExplorer";
import { ReviewPanel } from "./pages/ReviewPanel";

export default function App() {
  return (
    <Routes>
      <Route element={<Dashboard />} path="/" />
      <Route element={<BusinessProfile />} path="/entity/:ubid" />
      <Route element={<GraphExplorer />} path="/graph" />
      <Route element={<PincodeExplorer />} path="/pincodes" />
      <Route
        element={
          <ProtectedRoute roles={["analyst", "admin"]}>
            <ReviewPanel />
          </ProtectedRoute>
        }
        path="/review"
      />
      <Route element={<Navigate replace to="/" />} path="*" />
    </Routes>
  );
}
