/**
 * Single API client for the whole frontend.
 *
 * Previously twelve components each hardcoded `http://localhost:8000` (some
 * as `127.0.0.1`, which is a different CORS origin and failed independently).
 * That made the build impossible to deploy: there was no way to point the
 * bundle at a hosted API without editing a dozen files.
 *
 * The base URL now comes from VITE_API_BASE_URL at build time, and the bearer
 * token is attached centrally so no component has to remember to do it.
 */

const BASE_URL: string =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

const TOKEN_KEY = "tracker.token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string | null): void {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public detail?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Content-Type", "application/json");

  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch(`${BASE_URL}${path}`, { ...init, headers });

  if (response.status === 401) {
    // The token is gone or expired. Clear it so the UI shows a login prompt
    // rather than looping on failed authenticated requests.
    setToken(null);
    throw new ApiError(401, "Your session has expired. Please sign in again.");
  }

  if (!response.ok) {
    let detail: unknown;
    try {
      detail = (await response.json())?.detail;
    } catch {
      detail = await response.text();
    }
    throw new ApiError(
      response.status,
      typeof detail === "string" ? detail : `Request failed (${response.status})`,
      detail,
    );
  }

  return response.status === 204 ? (undefined as T) : ((await response.json()) as T);
}

// ---- Types -----------------------------------------------------------------

export interface Forecast {
  model: string;
  source: string;
  horizon_days: number;
  as_of: string;
  target_date: string;
  anchor_price: number;
  predicted_price: number;
  lower_price: number;
  upper_price: number;
  expected_change_pct: number;
  confidence_level: number;
  model_family: string;
  history_points: number;
}

export interface LivePrice {
  model: string;
  source: string;
  price: number;
  previous_price: number | null;
  change_pct: number | null;
  rating: number | null;
  observed_at: string;
  url: string | null;
}

export interface CollectionResult {
  model: string;
  source: string;
  status: string;
  price: number | null;
  method: string | null;
  message: string;
}

export interface CollectionStatus {
  scheduler: {
    collect_interval_minutes: number;
    next_collection_at: string | null;
    retrain_interval_hours: number;
    next_retrain_at: string | null;
  };
  live_history_days: Record<string, number>;
  latest_run: {
    id: number;
    status: string;
    stored: number;
    targets: number;
    started_at: string;
    finished_at: string | null;
  } | null;
  latest_run_results: CollectionResult[];
}

export interface ModelCard {
  trained_at: string;
  data_source: string;
  horizons: Record<
    string,
    {
      selected_model: string;
      mae_rupees: number;
      mape: number;
      beats_naive_baseline: boolean;
      improvement_over_baseline: number;
      interval_coverage: number;
    }
  >;
}

export interface Alert {
  id: number;
  model: string;
  source: string;
  event_type: string;
  severity: string;
  message: string;
  created_at: string;
}

export interface AuthResult {
  access_token: string;
  name: string;
  email: string;
  role: "user" | "admin";
  expires_in_minutes: number;
}

// ---- Endpoints -------------------------------------------------------------

export const api = {
  health: () => request<{ status: string }>("/health"),

  signup: async (name: string, email: string, password: string) => {
    const result = await request<AuthResult>("/api/auth/signup", {
      method: "POST",
      body: JSON.stringify({ name, email, password }),
    });
    setToken(result.access_token);
    return result;
  },

  login: async (email: string, password: string) => {
    const result = await request<AuthResult>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    setToken(result.access_token);
    return result;
  },

  logout: () => setToken(null),

  me: () => request<{ email: string; role: string }>("/api/auth/me"),

  series: () => request<{ series: unknown[] }>("/api/series"),

  forecast: (model: string, source: string, horizonDays = 14) =>
    request<Forecast>("/api/forecast", {
      method: "POST",
      body: JSON.stringify({ model, source, horizon_days: horizonDays }),
    }),

  compare: (model: string, horizonDays = 14) =>
    request<{
      forecasts: Record<string, Forecast>;
      cheapest_forecast: string;
      forecast_spread: number | null;
    }>(`/api/compare/${encodeURIComponent(model)}?horizon_days=${horizonDays}`),

  recommendPrice: (body: {
    model: string;
    source: string;
    horizon_days?: number;
    unit_cost?: number;
  }) =>
    request<{ forecast: Forecast; recommendation: Record<string, unknown> }>(
      "/api/pricing/recommend",
      { method: "POST", body: JSON.stringify(body) },
    ),

  anomalies: (model: string, source: string) =>
    request<{ event_count: number; events: unknown[] }>(
      `/api/anomalies/${encodeURIComponent(model)}/${encodeURIComponent(source)}`,
    ),

  modelCard: () => request<ModelCard>("/api/model-card"),

  latestPrices: () => request<{ prices: LivePrice[] }>("/api/prices/latest"),

  priceHistory: (model: string, source: string, days = 90) =>
    request<{ points: { date: string; price: number }[] }>(
      `/api/prices/history/${encodeURIComponent(model)}/${encodeURIComponent(source)}?days=${days}`,
    ),

  reviews: (model: string, limit = 30) =>
    request<{ reviews: { source: string; rating: number | null; review: string; observed_at: string }[] }>(
      `/api/reviews/${encodeURIComponent(model)}?limit=${limit}`,
    ),

  collectStatus: () => request<CollectionStatus>("/api/collect/status"),

  runCollection: () =>
    request<{ status: string }>("/api/collect/run", { method: "POST" }),

  retrain: () => request<{ status: string }>("/api/model/retrain", { method: "POST" }),

  accuracy: () => request<Record<string, unknown>>("/api/accuracy"),

  alerts: (unacknowledgedOnly = false) =>
    request<{ alerts: Alert[] }>(
      `/api/alerts?unacknowledged_only=${unacknowledgedOnly}`,
    ),

  acknowledgeAlert: (id: number) =>
    request<{ message: string }>(`/api/alerts/${id}/acknowledge`, {
      method: "POST",
    }),

  scanAlerts: () =>
    request<{ alerts_created: number }>("/api/alerts/scan", { method: "POST" }),

  products: (limit = 50, offset = 0) =>
    request<{ total: number; products: unknown[] }>(
      `/api/products?limit=${limit}&offset=${offset}`,
    ),

  createProduct: (body: Record<string, unknown>) =>
    request<{ id: number }>("/api/products", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  updateProduct: (id: number, body: Record<string, unknown>) =>
    request<{ message: string }>(`/api/products/${id}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),

  deleteProduct: (id: number) =>
    request<{ message: string }>(`/api/products/${id}`, { method: "DELETE" }),

  assistant: (message: string) =>
    request<{ reply: string; data: unknown; grounded: boolean }>(
      "/api/assistant",
      { method: "POST", body: JSON.stringify({ message }) },
    ),
};
