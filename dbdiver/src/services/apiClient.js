const BASE_URL = import.meta?.env?.VITE_API_URL || 'http://localhost:8000';

async function jsonFetch(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: 'GET',
    headers: { 
      'Content-Type': 'application/json',
      ...(options.headers || {})
    },
    ...options,
    body: options.body ? JSON.stringify(options.body) : undefined,
  });

  let data = null;
  try {
    data = await res.json();
  } catch {
    // ignore parse error
  }

  if (!res.ok) {
    const msg = data?.detail || data?.message || `HTTP ${res.status}`;
    throw new Error(msg);
  }
  return data;
}

export const api = {
  async getRagOverview() {
    return jsonFetch('/api/rag-overview');
  },

  async askQuery({ query, database }) {
    return jsonFetch('/api/query', {
      method: 'POST',
      body: { query, database: database || undefined },
    });
  },

  async executeSql({ sql_query, database }) {
    return jsonFetch('/api/execute-sql', {
      method: 'POST',
      body: { sql_query, database },
    });
  },

  async getConnections() {
    return jsonFetch('/api/connections');
  },
};