const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api";

async function request(path, { token, method = "GET", body } = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    },
    body: body ? JSON.stringify(body) : undefined
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = typeof payload.detail === "string"
      ? payload.detail
      : payload.detail
        ? JSON.stringify(payload.detail)
        : "API request failed.";
    throw new Error(detail);
  }
  return payload;
}

export const api = {
  login: (credentials) => request("/auth/login", { method: "POST", body: credentials }),
  me: (token) => request("/auth/me", { token }),
  inventoryItems: (token) => request("/inventory/items", { token }),
  inventorySummary: (token) => request("/inventory/summary", { token }),
  analyze: (token, body) => request("/workflows/analyze", { token, method: "POST", body }),
  chat: async (token, message, inventoryContext = null) => {
    return request("/rag/chat", {
      token,
      method: "POST",
      body: { message, inventory_context: inventoryContext }
    });
  }
};
