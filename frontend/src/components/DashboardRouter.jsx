import { AdminDashboard } from "./dashboards/AdminDashboard";
import { ExecutiveDashboard } from "./dashboards/ExecutiveDashboard";
import { PharmacistDashboard } from "./dashboards/PharmacistDashboard";

export function DashboardRouter({ analysis }) {
  if (analysis.role === "admin") return <AdminDashboard analysis={analysis} />;
  if (analysis.role === "executive") return <ExecutiveDashboard analysis={analysis} />;
  return <PharmacistDashboard analysis={analysis} />;
}

