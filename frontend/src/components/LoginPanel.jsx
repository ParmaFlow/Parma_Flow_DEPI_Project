import { useState } from "react";
import { LockKeyhole } from "lucide-react";

import { api } from "../api/client";

const users = [
  { label: "Admin", username: "admin", password: "admin123" },
  { label: "Pharmacist", username: "pharmacist", password: "ops123" },
  { label: "Executive", username: "executive", password: "exec123" }
];

export function LoginPanel({ onLogin }) {
  const [selected, setSelected] = useState(users[1]);
  const [password, setPassword] = useState(users[1].password);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const auth = await api.login({ username: selected.username, password });
      onLogin(auth);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function chooseUser(user) {
    setSelected(user);
    setPassword(user.password);
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-100 px-4 py-10">
      <form onSubmit={submit} className="w-full max-w-md rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <div className="mb-6 flex flex-col items-center gap-4 text-center">
          <img src="/logo.svg" alt="Pharma-Flow Logo" className="h-16 w-auto" />
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Pharma-Flow AI</p>
            <h1 className="text-xl font-semibold text-ink">MVP Access</h1>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-2">
          {users.map((user) => (
            <button
              key={user.username}
              type="button"
              onClick={() => chooseUser(user)}
              className={`focus-ring h-10 rounded-md border text-sm font-semibold ${
                selected.username === user.username
                  ? "border-clinical bg-blue-50 text-clinical"
                  : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
              }`}
            >
              {user.label}
            </button>
          ))}
        </div>

        <label className="mt-5 block text-sm font-medium text-slate-700">
          Password
          <input
            className="focus-ring mt-2 h-11 w-full rounded-md border border-slate-300 px-3 text-ink"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </label>

        {error ? <p className="mt-3 rounded-md bg-red-50 p-3 text-sm font-medium text-red-800">{error}</p> : null}

        <button
          type="submit"
          disabled={loading}
          className="focus-ring mt-5 h-11 w-full rounded-md bg-clinical px-4 text-sm font-semibold text-white hover:bg-blue-800 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? "Signing in" : "Sign in"}
        </button>
      </form>
    </main>
  );
}

