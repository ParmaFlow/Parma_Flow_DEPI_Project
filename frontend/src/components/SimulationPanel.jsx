import { RefreshCw, Package, Tag, MapPin, Box, TrendingUp, Clock, AlertTriangle, ArrowUpRight, ArrowDownRight } from "lucide-react";

const numberFields = [
  ["available_stock", "Current stock", <Box className="h-4 w-4" />],
  ["forecast_demand", "Forecast demand", <TrendingUp className="h-4 w-4" />],
  ["lead_time", "Lead time", <Clock className="h-4 w-4" />],
  ["expiry_days", "Shelf life", <AlertTriangle className="h-4 w-4" />],
  ["confidence_low", "Forecast low", <ArrowDownRight className="h-4 w-4" />],
  ["confidence_high", "Forecast high", <ArrowUpRight className="h-4 w-4" />]
];

export function SimulationPanel({ value, inventory, loading, onChange, onSelectSku, onAnalyze }) {
  function update(field, nextValue) {
    const parsed = field === "sku_name" || field === "location_type" ? nextValue : Number(nextValue);
    onChange({ ...value, [field]: parsed });
  }

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <div className="mb-6 flex items-center gap-2 border-b border-slate-100 pb-4">
        <div className="flex h-8 w-8 items-center justify-center rounded-md bg-blue-50 text-clinical">
          <RefreshCw className="h-4 w-4" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-ink">Inventory Simulator</h2>
          <p className="text-xs text-slate-500">Adjust variables to run AI predictions</p>
        </div>
      </div>

      <div className="space-y-5">
        <label className="block text-sm font-medium text-slate-700">
          <div className="flex items-center gap-1.5 mb-2 text-slate-600">
            <Tag className="h-4 w-4" />
            <span>Select SKU</span>
          </div>
          <select
            value={value.sku || ""}
            onChange={(event) => onSelectSku(event.target.value)}
            className="focus-ring h-10 w-full rounded-md border border-slate-300 bg-slate-50 px-3 text-sm transition-colors hover:bg-white focus:bg-white"
          >
            <option value={value.sku}>{value.sku_name}</option>
            {inventory.map((item) => (
              <option key={item.sku_id} value={item.sku_id}>
                {item.sku_id} - {item.generic_name}
              </option>
            ))}
          </select>
        </label>

        <div className="grid grid-cols-2 gap-4">
          <label className="block text-sm font-medium text-slate-700">
            <div className="flex items-center gap-1.5 mb-2 text-slate-600">
              <Package className="h-4 w-4" />
              <span>Medication Name</span>
            </div>
            <input
              value={value.sku_name}
              onChange={(event) => update("sku_name", event.target.value)}
              className="focus-ring h-10 w-full rounded-md border border-slate-300 bg-slate-50 px-3 text-sm transition-colors focus:bg-white"
            />
          </label>

          <label className="block text-sm font-medium text-slate-700">
            <div className="flex items-center gap-1.5 mb-2 text-slate-600">
              <MapPin className="h-4 w-4" />
              <span>Location</span>
            </div>
            <select
              value={value.location_type}
              onChange={(event) => update("location_type", event.target.value)}
              className="focus-ring h-10 w-full rounded-md border border-slate-300 bg-slate-50 px-3 text-sm transition-colors hover:bg-white focus:bg-white"
            >
              <option value="hospital">Hospital</option>
              <option value="warehouse">Warehouse</option>
            </select>
          </label>
        </div>

        <div className="pt-4 mt-4 border-t border-slate-100">
          <h3 className="text-sm font-semibold text-slate-600 mb-4">Metrics & Forecasts</h3>
          <div className="grid grid-cols-2 gap-4">
            {numberFields.map(([field, label, icon]) => (
              <label key={field} className="block text-sm font-medium text-slate-700">
                <div className="flex items-center gap-1.5 mb-2 text-slate-500">
                  {icon}
                  <span>{label}</span>
                </div>
                <input
                  type="number"
                  value={value[field]}
                  onChange={(event) => update(field, event.target.value)}
                  className="focus-ring h-10 w-full rounded-md border border-slate-300 bg-white px-3 text-sm font-mono"
                />
              </label>
            ))}
          </div>
        </div>

        <div className="pt-2">
          <button
            type="button"
            onClick={onAnalyze}
            disabled={loading}
            className="flex h-11 w-full items-center justify-center gap-2 rounded-md bg-clinical text-sm font-medium text-white shadow-sm transition-colors hover:bg-blue-700 disabled:bg-slate-300 focus:outline-none focus:ring-4 focus:ring-blue-100"
          >
            {loading ? (
              <RefreshCw className="h-5 w-5 animate-spin" />
            ) : (
              <>
                <RefreshCw className="h-4 w-4" />
                Run AI Analysis
              </>
            )}
          </button>
        </div>
      </div>
    </section>
  );
}
