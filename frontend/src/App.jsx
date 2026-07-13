import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, BarChart3, LogOut, RefreshCw, ShieldCheck, Package, TrendingUp } from "lucide-react";

import { api } from "./api/client";
import { DashboardRouter } from "./components/DashboardRouter";
import { LoginPanel } from "./components/LoginPanel";
import { MetricCard } from "./components/MetricCard";
import { RoleBadge } from "./components/RoleBadge";
import { Shell } from "./components/Shell";
import { SimulationPanel } from "./components/SimulationPanel";
import { FloatingChatWidget } from "./components/FloatingChatWidget";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar, AreaChart, Area } from "recharts";

const demandData = [
  { name: 'Jan', demand: 400 },
  { name: 'Feb', demand: 450 },
  { name: 'Mar', demand: 300 },
  { name: 'Apr', demand: 500 },
  { name: 'May', demand: 550 },
  { name: 'Jun', demand: 600 },
];
const riskData = [
  { name: 'Low Risk', value: 65 },
  { name: 'Medium Risk', value: 25 },
  { name: 'Critical', value: 10 },
];
const shortageData = [
  { name: 'Paracetamol', shortage: 150 },
  { name: 'Ibuprofen', shortage: 120 },
  { name: 'Amoxicillin', shortage: 80 },
  { name: 'Aspirin', shortage: 50 },
];
const stockLevelData = [
  { month: 'Jan', stock: 1200, reorderPoint: 800 },
  { month: 'Feb', stock: 900, reorderPoint: 800 },
  { month: 'Mar', stock: 650, reorderPoint: 800 },
  { month: 'Apr', stock: 1100, reorderPoint: 800 },
  { month: 'May', stock: 950, reorderPoint: 800 },
  { month: 'Jun', stock: 750, reorderPoint: 800 },
];
const COLORS = ['#0080FF', '#b45309', '#b91c1c'];

const defaultCase = {
  sku: "PARA-500",
  sku_name: "Paracetamol",
  location_type: "hospital",
  available_stock: 0,
  forecast_demand: 500,
  lead_time: 10,
  expiry_days: 60,
  confidence_low: 400,
  confidence_high: 650,
  on_order: 0
};

export default function App() {
  const [token, setToken] = useState(localStorage.getItem("pharmaflow_token") || "");
  const [user, setUser] = useState(null);
  const [inventory, setInventory] = useState([]);
  const [summary, setSummary] = useState(null);
  const [caseInput, setCaseInput] = useState(defaultCase);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [currentTab, setCurrentTab] = useState("simulator");

  useEffect(() => {
    if (!token) return;
    api.me(token)
      .then(setUser)
      .catch(() => {
        localStorage.removeItem("pharmaflow_token");
        setToken("");
      });
  }, [token]);

  useEffect(() => {
    if (!token) return;
    Promise.all([api.inventoryItems(token), api.inventorySummary(token)])
      .then(([items, dataSummary]) => {
        setInventory(items);
        setSummary(dataSummary);
      })
      .catch((err) => setError(err.message));
  }, [token]);

  const selectedInventoryItem = useMemo(() => {
    return inventory.find((item) => item.sku_id === caseInput.sku);
  }, [inventory, caseInput.sku]);

  const totalStock = useMemo(() => {
    return inventory.reduce((sum, item) => sum + Number(item.stock || 0), 0);
  }, [inventory]);

  const itemsAtRisk = useMemo(() => {
    return inventory.filter(item => Number(item.stock || 0) <= Number(item.reorder_point || item.forecast_demand || 0)).length;
  }, [inventory]);

  const totalDemand = useMemo(() => {
    return inventory.reduce((sum, item) => sum + Number(item.forecast_demand || 0), 0);
  }, [inventory]);

  function exportToCSV() {
    if (!inventory || inventory.length === 0) return;
    const headers = ["SKU ID", "Generic Name", "Stock", "Forecast Demand", "Lead Time", "Expiry Days"];
    const csvContent = [
      headers.join(","),
      ...inventory.map(item => [
        item.sku_id,
        `"${item.generic_name || ""}"`,
        item.stock || 0,
        item.forecast_demand || 0,
        item.lead_time || 0,
        item.expiry_days || 0
      ].join(","))
    ].join("\n");

    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", `pharmaflow_inventory_report_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  function handleLogin(auth) {
    localStorage.setItem("pharmaflow_token", auth.access_token);
    setToken(auth.access_token);
    setUser(auth.user);
  }

  function handleLogout() {
    localStorage.removeItem("pharmaflow_token");
    setToken("");
    setUser(null);
    setAnalysis(null);
  }

  function handleSelectSku(skuId) {
    const item = inventory.find((entry) => entry.sku_id === skuId);
    if (!item) return;
    setCaseInput((current) => ({
      ...current,
      sku: item.sku_id || current.sku,
      sku_name: item.generic_name || current.sku_name,
      available_stock: Number(item.stock ?? current.available_stock),
      forecast_demand: Number(item.forecast_demand ?? current.forecast_demand),
      expiry_days: Number(item.expiry_days ?? current.expiry_days)
    }));
  }

  async function handleAnalyze() {
    setLoading(true);
    setError("");
    try {
      const result = await api.analyze(token, caseInput);
      setAnalysis(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  if (!token || !user) {
    return <LoginPanel onLogin={handleLogin} />;
  }

  return (
    <Shell
      user={user}
      onLogout={handleLogout}
    >
      <div className="mb-6 flex items-center justify-between border-b border-slate-200">
        <nav className="-mb-px flex space-x-8" aria-label="Tabs">
          <button
            onClick={() => setCurrentTab('simulator')}
            className={`whitespace-nowrap border-b-2 px-1 py-4 text-sm font-medium ${
              currentTab === 'simulator'
                ? 'border-clinical text-clinical'
                : 'border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700'
            }`}
          >
            Inventory Simulator
          </button>
          <button
            onClick={() => setCurrentTab('analytics')}
            className={`whitespace-nowrap border-b-2 px-1 py-4 text-sm font-medium ${
              currentTab === 'analytics'
                ? 'border-clinical text-clinical'
                : 'border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700'
            }`}
          >
            Analytics Dashboard
          </button>
        </nav>
        {currentTab === 'analytics' && (
          <button
            onClick={exportToCSV}
            className="focus-ring inline-flex h-9 items-center gap-2 rounded-md border border-slate-300 bg-white px-3 text-sm font-medium text-slate-700 shadow-sm transition-colors hover:bg-slate-50"
          >
            <svg className="h-4 w-4 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            Export CSV
          </button>
        )}
      </div>

      {currentTab === 'simulator' && (
        <div className="grid gap-4 lg:grid-cols-[360px_minmax(0,1fr)]">
          <aside className="space-y-4">
            <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
              <div className="mb-4 flex items-center justify-between">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Session</p>
                  <h2 className="text-lg font-semibold text-ink">{user.display_name}</h2>
                </div>
                <RoleBadge role={user.role} />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <MetricCard icon={BarChart3} label="SKUs" value={summary?.sku_count ?? "-"} />
                <MetricCard icon={AlertTriangle} label="Shortage watch" value={summary?.shortage_candidates ?? "-"} tone="amber" />
              </div>
            </div>

            <SimulationPanel
              value={caseInput}
              inventory={inventory}
              selectedInventoryItem={selectedInventoryItem}
              loading={loading}
              onChange={setCaseInput}
              onSelectSku={handleSelectSku}
              onAnalyze={handleAnalyze}
            />
          </aside>

          <main className="min-w-0 space-y-4">
            {error ? (
              <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm font-medium text-red-800">
                {error}
              </div>
            ) : null}

            {!analysis ? (
              <section className="rounded-lg border border-slate-200 bg-white p-8 shadow-sm">
                <div className="flex max-w-2xl items-start gap-4">
                  <div className="flex h-12 w-12 items-center justify-center rounded-md bg-blue-50 text-clinical">
                    <ShieldCheck className="h-6 w-6" />
                  </div>
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Ready</p>
                    <h1 className="mt-1 text-2xl font-semibold text-ink">Run a multi-agent inventory decision</h1>
                    <p className="mt-2 text-sm leading-6 text-slate-600">
                      The API will execute OpsAgent, RiskAgent, AuditorAgent, and ReportAgent, then return the dashboard view for your role.
                    </p>
                    <button
                      type="button"
                      onClick={handleAnalyze}
                      disabled={loading}
                      className="focus-ring mt-5 inline-flex h-10 items-center gap-2 rounded-md bg-clinical px-4 text-sm font-semibold text-white hover:bg-blue-800 disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
                      Run analysis
                    </button>
                  </div>
                </div>
              </section>
            ) : (
              <DashboardRouter analysis={analysis} />
            )}
          </main>
        </div>
      )}

      {currentTab === 'analytics' && (
        <div className="space-y-6">
          <div className="grid gap-4 md:grid-cols-3">
            <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
                  <Package className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-sm font-medium text-slate-500">Total Stock Items</p>
                  <p className="text-2xl font-bold text-ink">{totalStock.toLocaleString()}</p>
                </div>
              </div>
            </div>
            <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-red-50 text-red-600">
                  <AlertTriangle className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-sm font-medium text-slate-500">Items at Risk</p>
                  <p className="text-2xl font-bold text-ink">{itemsAtRisk}</p>
                </div>
              </div>
            </div>
            <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-green-50 text-green-600">
                  <TrendingUp className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-sm font-medium text-slate-500">Total Demand Forecast</p>
                  <p className="text-2xl font-bold text-ink">{totalDemand.toLocaleString()}</p>
                </div>
              </div>
            </div>
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-ink mb-4">6-Month Demand Forecast</h2>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={demandData}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="name" axisLine={false} tickLine={false} />
                    <YAxis axisLine={false} tickLine={false} />
                    <RechartsTooltip />
                    <Line type="monotone" dataKey="demand" stroke="#0080FF" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
            
            <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-ink mb-4">Inventory Risk Distribution</h2>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={riskData}
                      cx="50%"
                      cy="50%"
                      innerRadius={80}
                      outerRadius={100}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {riskData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <RechartsTooltip />
                    <Legend verticalAlign="bottom" height={36} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
            
            <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-ink mb-4">Top Shortage Alerts</h2>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={shortageData} layout="vertical" margin={{ left: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                    <XAxis type="number" axisLine={false} tickLine={false} />
                    <YAxis dataKey="name" type="category" axisLine={false} tickLine={false} />
                    <RechartsTooltip cursor={{ fill: '#f1f5f9' }} />
                    <Bar dataKey="shortage" fill="#b91c1c" radius={[0, 4, 4, 0]} barSize={24} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-ink mb-4">Stock vs Reorder Point</h2>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={stockLevelData}>
                    <defs>
                      <linearGradient id="colorStock" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#0080FF" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#0080FF" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="month" axisLine={false} tickLine={false} />
                    <YAxis axisLine={false} tickLine={false} />
                    <RechartsTooltip />
                    <Legend verticalAlign="bottom" height={36} />
                    <Area type="monotone" dataKey="stock" stroke="#0080FF" fillOpacity={1} fill="url(#colorStock)" />
                    <Line type="monotone" dataKey="reorderPoint" stroke="#b45309" strokeDasharray="5 5" dot={false} strokeWidth={2} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </div>
      )}

      <FloatingChatWidget token={token} inventory={inventory} />
    </Shell>
  );
}

