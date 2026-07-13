import { AdminDashboard } from "./dashboards/AdminDashboard";
import { ExecutiveDashboard } from "./dashboards/ExecutiveDashboard";
import { PharmacistDashboard } from "./dashboards/PharmacistDashboard";

export function DashboardRouter({ analysis }) {
  const safeAnalysis = analysis || {};
  if (safeAnalysis.role === "admin") return <AdminDashboard analysis={safeAnalysis} />;
  if (safeAnalysis.role === "executive") return <ExecutiveDashboard analysis={safeAnalysis} />;
  return <PharmacistDashboard analysis={safeAnalysis} />;
}
