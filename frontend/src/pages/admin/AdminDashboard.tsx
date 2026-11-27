import {
  Activity,
  AlertCircle,
  ArrowDownRight,
  ArrowUpRight,
  Brain,
  RefreshCw,
  Radio,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Button } from "../../components/ui/button";
import UploadModel from "../../components/Layout/UploadModel";
import {
  api,
  type Alert,
  type CollectionStatus,
  type Forecast,
  type LivePrice,
  type ModelCard,
} from "../../lib/api";

const MODELS = ["iPhone 15", "iPhone 16", "iPhone 17"];
const REFRESH_MS = 60_000;

const inr = new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 });
const rupees = (value: number | null | undefined) =>
  value == null ? "—" : `₹${inr.format(value)}`;
const ago = (iso: string | null | undefined) => {
  if (!iso) return "never";
  const stamp = new Date(iso.endsWith("Z") || iso.includes("+") ? iso : `${iso}Z`);
  const minutes = Math.round((Date.now() - stamp.getTime()) / 60_000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.round(minutes / 60);
  return hours < 48 ? `${hours} h ago` : `${Math.round(hours / 24)} days ago`;
};

const STATUS_STYLE: Record<string, string> = {
  ok: "bg-green-100 text-green-700",
  partial: "bg-amber-100 text-amber-700",
  rejected: "bg-amber-100 text-amber-700",
  blocked: "bg-red-100 text-red-700",
  throttled: "bg-red-100 text-red-700",
  disallowed: "bg-red-100 text-red-700",
  failed: "bg-red-100 text-red-700",
};

export const AdminDashboard = () => {
  const [prices, setPrices] = useState<LivePrice[]>([]);
  const [status, setStatus] = useState<CollectionStatus | null>(null);
  const [card, setCard] = useState<ModelCard | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [forecasts, setForecasts] = useState<Record<string, Record<string, Forecast>>>({});
  const [horizon, setHorizon] = useState(14);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState<string | null>(null);
  const [isRetrainOpen, setIsRetrainOpen] = useState(false);
  const [collecting, setCollecting] = useState(false);

  const load = useCallback(async () => {
    // Each panel loads independently, so one failing endpoint never blanks
    // the whole page.
    const [p, s, c, a] = await Promise.allSettled([
      api.latestPrices(),
      api.collectStatus(),
      api.modelCard(),
      api.alerts(),
    ]);
    if (p.status === "fulfilled") setPrices(p.value.prices);
    if (s.status === "fulfilled") setStatus(s.value);
    if (c.status === "fulfilled") setCard(c.value);
    if (a.status === "fulfilled") setAlerts(a.value.alerts.slice(0, 6));

    const compared = await Promise.allSettled(MODELS.map((m) => api.compare(m, horizon)));
    const next: Record<string, Record<string, Forecast>> = {};
    compared.forEach((result, i) => {
      if (result.status === "fulfilled") next[MODELS[i]] = result.value.forecasts;
    });
    setForecasts(next);
    setLoading(false);
  }, [horizon]);

  useEffect(() => {
    load();
    const timer = window.setInterval(load, REFRESH_MS);
    return () => window.clearInterval(timer);
  }, [load]);

  const collectNow = async () => {
    setCollecting(true);
    setMessage(null);
    try {
      await api.runCollection();
      setMessage("Collection started. New prices appear here within a minute.");
      window.setTimeout(load, 45_000);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not start collection.");
    } finally {
      setCollecting(false);
    }
  };

  const run = status?.latest_run;
  const scheduler = status?.scheduler;

  return (
    <div className="p-6 space-y-8 bg-white text-black min-h-screen">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Live Competitor Prices</h1>
          <p className="text-gray-600 flex items-center gap-2">
            <Radio className="w-4 h-4 text-green-600" />
            {run
              ? `Last collection ${ago(run.finished_at || run.started_at)}: ${run.stored} of ${run.targets} prices stored`
              : "No live collection has run yet"}
            {scheduler?.collect_interval_minutes
              ? ` · next run ${ago(scheduler.next_collection_at).replace(" ago", "")}`
              : " · scheduler off"}
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={collectNow}
            disabled={collecting}
            className="bg-gradient-to-r from-blue-500 to-blue-600 text-white px-4 py-2 rounded-lg hover:shadow-lg"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${collecting ? "animate-spin" : ""}`} />
            Collect now
          </Button>
          <Button variant="outline" onClick={() => setIsRetrainOpen(true)} className="px-4 py-2 rounded-lg">
            <Brain className="w-4 h-4 mr-2" />
            Retrain
          </Button>
        </div>
      </div>

      {message && (
        <div className="p-3 rounded-lg bg-blue-50 border border-blue-100 text-sm text-blue-700">{message}</div>
      )}

      {/* Live prices */}
      <section>
        <h2 className="text-xl font-bold text-gray-900 mb-4">Latest scraped prices</h2>
        {loading ? (
          <p className="text-gray-500">Loading…</p>
        ) : prices.length === 0 ? (
          <p className="text-gray-500">No prices stored yet. Click "Collect now" or enable the scheduler.</p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {prices.map((p) => (
              <div key={`${p.model}-${p.source}`} className="rounded-xl p-5 border border-gray-200 shadow-sm">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm text-gray-600">
                    {p.model} · {p.source}
                  </p>
                  {p.change_pct != null && p.change_pct !== 0 && (
                    <span
                      className={`flex items-center text-sm font-medium ${
                        p.change_pct < 0 ? "text-green-600" : "text-red-600"
                      }`}
                    >
                      {p.change_pct < 0 ? <ArrowDownRight className="w-4 h-4" /> : <ArrowUpRight className="w-4 h-4" />}
                      {Math.abs(p.change_pct).toFixed(2)}%
                    </span>
                  )}
                </div>
                <p className="text-2xl font-bold text-gray-900 tabular-nums">{rupees(p.price)}</p>
                <p className="text-xs text-gray-500 mt-1">
                  Seen {ago(p.observed_at)}
                  {p.rating ? ` · ★ ${p.rating.toFixed(1)}` : ""}
                  {p.url && (p.url.startsWith("https://") || p.url.startsWith("http://")) && (
                    <>
                      {" · "}
                      <a href={p.url} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline">
                        listing
                      </a>
                    </>
                  )}
                </p>
              </div>
            ))}
          </div>
        )}
      </section>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Forecasts */}
        <section className="lg:col-span-2 border border-gray-200 rounded-xl p-6 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
            <h2 className="text-xl font-bold text-gray-900">Forecasts</h2>
            <div className="inline-flex rounded-lg border border-gray-200 overflow-hidden text-sm">
              {[7, 14, 30].map((h) => (
                <button
                  key={h}
                  onClick={() => setHorizon(h)}
                  className={`px-3 py-1.5 ${horizon === h ? "bg-gray-900 text-white" : "bg-white text-gray-700"}`}
                >
                  {h} days
                </button>
              ))}
            </div>
          </div>
          {Object.keys(forecasts).length === 0 ? (
            <p className="text-gray-500 text-sm">
              Forecasts need about 20 days of history per series. They appear here automatically once the
              collector has gathered enough.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm tabular-nums">
                <thead>
                  <tr className="text-left text-gray-500 border-b">
                    <th className="py-2 pr-3">Series</th>
                    <th className="py-2 pr-3 text-right">Now</th>
                    <th className="py-2 pr-3 text-right">Forecast</th>
                    <th className="py-2 pr-3 text-right">80% range</th>
                    <th className="py-2 text-right">Change</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(forecasts).flatMap(([model, bySource]) =>
                    Object.values(bySource).map((f) => (
                      <tr key={`${model}-${f.source}`} className="border-b last:border-0">
                        <td className="py-2 pr-3">
                          {model} · {f.source}
                        </td>
                        <td className="py-2 pr-3 text-right">{rupees(f.anchor_price)}</td>
                        <td className="py-2 pr-3 text-right font-medium">{rupees(f.predicted_price)}</td>
                        <td className="py-2 pr-3 text-right text-gray-500">
                          {rupees(f.lower_price)} – {rupees(f.upper_price)}
                        </td>
                        <td className={`py-2 text-right ${f.expected_change_pct < 0 ? "text-green-600" : "text-red-600"}`}>
                          {f.expected_change_pct > 0 ? "+" : ""}
                          {f.expected_change_pct.toFixed(1)}%
                        </td>
                      </tr>
                    )),
                  )}
                </tbody>
              </table>
            </div>
          )}
        </section>

        {/* Alerts */}
        <section className="border border-gray-200 rounded-xl p-6 shadow-sm">
          <h2 className="text-xl font-bold flex items-center mb-4 text-gray-900">
            <AlertCircle className="h-5 w-5 mr-2 text-blue-500" />
            Price alerts
          </h2>
          {alerts.length === 0 ? (
            <p className="text-sm text-gray-500">No price changes over 1% detected yet.</p>
          ) : (
            <ul className="space-y-3">
              {alerts.map((a) => (
                <li key={a.id} className="p-3 rounded-lg bg-gray-50 border border-gray-100">
                  <p className="text-sm text-gray-800">{a.message}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    {a.event_type.replace(/_/g, " ")} · {ago(a.created_at)}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Collector health */}
        <section className="border border-gray-200 rounded-xl p-6 shadow-sm">
          <h2 className="text-xl font-bold flex items-center mb-4 text-gray-900">
            <Activity className="h-5 w-5 mr-2 text-blue-500" />
            Collector, last run
          </h2>
          {!status?.latest_run_results?.length ? (
            <p className="text-sm text-gray-500">No runs recorded yet.</p>
          ) : (
            <ul className="space-y-2 text-sm">
              {status.latest_run_results.map((r) => (
                <li key={`${r.model}-${r.source}`} className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-gray-800">
                      {r.model} · {r.source} {r.price ? `· ${rupees(r.price)}` : ""}
                    </p>
                    <p className="text-xs text-gray-500">{r.message}</p>
                  </div>
                  <span className={`px-2 py-0.5 rounded-full text-xs ${STATUS_STYLE[r.status] ?? "bg-gray-100 text-gray-700"}`}>
                    {r.status}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </section>

        {/* Model card */}
        <section className="border border-gray-200 rounded-xl p-6 shadow-sm">
          <h2 className="text-xl font-bold flex items-center mb-1 text-gray-900">
            <Brain className="h-5 w-5 mr-2 text-blue-500" />
            Forecast models
          </h2>
          {card ? (
            <>
              <p className="text-xs text-gray-500 mb-4">
                Trained {ago(card.trained_at)} on{" "}
                <span className={card.data_source === "live" ? "text-green-700" : "text-amber-700"}>
                  {card.data_source === "live" ? "live scraped data" : "synthetic bootstrap data"}
                </span>
                . Error measured on time-ordered test folds.
              </p>
              <table className="w-full text-sm tabular-nums">
                <thead>
                  <tr className="text-left text-gray-500 border-b">
                    <th className="py-2">Horizon</th>
                    <th className="py-2">Model</th>
                    <th className="py-2 text-right">Avg error</th>
                    <th className="py-2 text-right">vs. baseline</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(card.horizons).map(([h, m]) => (
                    <tr key={h} className="border-b last:border-0">
                      <td className="py-2">{h} days</td>
                      <td className="py-2">{m.selected_model === "lightgbm" ? "LightGBM" : "Random forest"}</td>
                      <td className="py-2 text-right">{rupees(m.mae_rupees)}</td>
                      <td className={`py-2 text-right ${m.beats_naive_baseline ? "text-green-600" : "text-red-600"}`}>
                        {(m.improvement_over_baseline * 100).toFixed(1)}% better
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          ) : (
            <p className="text-sm text-gray-500">Model card unavailable. Train the models first.</p>
          )}
        </section>
      </div>

      <UploadModel
        isOpen={isRetrainOpen}
        onClose={() => setIsRetrainOpen(false)}
        onSuccess={(msg) => {
          setMessage(msg);
          window.setTimeout(load, 90_000);
        }}
        onError={(msg) => setMessage(msg)}
      />
    </div>
  );
};
