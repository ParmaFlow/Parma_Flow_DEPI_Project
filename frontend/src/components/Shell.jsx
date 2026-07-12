import { UserCircle2 } from "lucide-react";

export function Shell({ user, onLogout, children }) {
  return (
    <div className="min-h-screen bg-slate-50 font-sans text-slate-900">
      <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-slate-200 bg-white px-6">
        <div className="flex items-center gap-2">
          <img src="/logo.svg" alt="Pharma-Flow Logo" className="h-10 w-auto" />
          <span className="text-xl font-bold tracking-tight text-ink">Pharma-Flow</span>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-sm">
            <UserCircle2 className="h-5 w-5 text-slate-400" />
            <div className="flex flex-col items-end">
              <span className="font-medium">{user.display_name}</span>
              <span className="text-xs text-slate-500 capitalize">{user.role}</span>
            </div>
          </div>
          <button
            onClick={onLogout}
            className="text-sm font-medium text-slate-500 hover:text-slate-700"
          >
            Logout
          </button>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {children}
      </main>
    </div>
  );
}
