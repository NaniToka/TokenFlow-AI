import React, { useEffect, useState } from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from 'recharts';
import Card from '../common/Card';
import { BarChart3, TrendingUp, DollarSign, Activity, DatabaseZap, Trash2, Calculator } from 'lucide-react';
import { getTelemetry, clearSemanticCache } from '../../services/api';

const PROJECTION_MODELS = [
  { id: 'gemini-1.5-flash', name: 'Gemini 1.5 Flash', ratePer1M: 0.075 },
  { id: 'gemini-1.5-pro', name: 'Gemini 1.5 Pro', ratePer1M: 1.25 },
  { id: 'gpt-4o', name: 'OpenAI GPT-4o', ratePer1M: 2.50 },
  { id: 'claude-3-5-sonnet', name: 'Claude 3.5 Sonnet', ratePer1M: 3.00 },
];

export default function AnalyticsCharts({ stats, onToast }) {
  const [telemetry, setTelemetry] = useState(null);
  const [monthlyRequests, setMonthlyRequests] = useState(500000);
  const requestHistory = stats?.request_history || [];

  const loadTelemetry = async () => {
    try {
      const data = await getTelemetry();
      setTelemetry(data);
    } catch {
      // ignore if offline
    }
  };

  useEffect(() => {
    loadTelemetry();
  }, [stats?.total_requests]);

  const handleClearCache = async () => {
    try {
      await clearSemanticCache();
      await loadTelemetry();
      onToast?.('Semantic summary & embedding caches flushed.');
    } catch {
      onToast?.('Failed to clear cache.', 'error');
    }
  };

  const chartData = requestHistory.map((item, index) => ({
    name: `#${item.id || index + 1}`,
    original: item.original_tokens || 0,
    compressed: item.compressed_tokens || 0,
    tokensSaved: item.tokens_saved || 0,
    costSaved: item.cost_saved_usd || 0,
    latency: item.latency_ms || 0,
  }));

  const percentiles = telemetry?.latency?.percentiles || { p50: 0, p90: 0, p95: 0, p99: 0 };
  const summaryCache = telemetry?.cache?.summary_cache || { hits: 0, misses: 0, hit_ratio_pct: 0, cached_entries: 0 };

  const avgSavedTokensPerReq =
    stats?.total_requests > 0 ? stats.total_tokens_saved / stats.total_requests : 250;

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="tf-card p-3 rounded-xl shadow-xl text-xs space-y-1.5 z-50">
          <p className="font-bold tf-text-primary pb-1" style={{ borderBottom: '1px solid var(--border-subtle)' }}>
            {label}
          </p>
          {payload.map((entry, index) => (
            <div key={index} className="flex items-center justify-between gap-4 font-mono">
              <span className="font-medium" style={{ color: entry.color }}>{entry.name}:</span>
              <span className="font-bold tf-text-primary">
                {typeof entry.value === 'number' && entry.value < 0.01 && entry.value > 0
                  ? `$${entry.value.toFixed(6)}`
                  : entry.value.toLocaleString()}
              </span>
            </div>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-6">
      {/* Latency Percentiles + Cache Telemetry Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
        <Card
          title="Runtime API Latency Percentiles"
          subtitle={`Measured across ${telemetry?.latency?.sample_size || 0} HTTP requests`}
          action={<Activity className="w-4 h-4 text-emerald-500" aria-hidden="true" />}
        >
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              { label: 'P50 Median', val: percentiles.p50, color: 'text-emerald-500' },
              { label: 'P90', val: percentiles.p90, color: 'text-cyan-500' },
              { label: 'P95 SLA', val: percentiles.p95, color: 'text-violet-500' },
              { label: 'P99 Tail', val: percentiles.p99, color: 'text-amber-500' },
            ].map((p) => (
              <div key={p.label} className="p-3 rounded-xl tf-subsurface text-center">
                <p className="text-[10px] font-bold uppercase tracking-wider tf-text-muted">{p.label}</p>
                <p className={`text-lg font-mono font-bold mt-1 ${p.color}`}>{p.val} ms</p>
              </div>
            ))}
          </div>
        </Card>

        <Card
          title="Semantic LRU Cache Telemetry"
          subtitle="SHA-256 prompt cache bypassing redundant summarization calls"
          action={
            <button
              type="button"
              onClick={handleClearCache}
              className="tf-btn-target flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-rose-500/10 text-rose-500 border border-rose-500/30 text-xs font-semibold cursor-pointer"
            >
              <Trash2 className="w-3.5 h-3.5" aria-hidden="true" /> Flush Cache
            </button>
          }
        >
          <div className="grid grid-cols-3 gap-3">
            <div className="p-3 rounded-xl tf-subsurface text-center">
              <p className="text-[10px] font-bold uppercase tf-text-muted">Hit Ratio</p>
              <p className="text-lg font-mono font-bold text-cyan-500 mt-1">{summaryCache.hit_ratio_pct}%</p>
            </div>
            <div className="p-3 rounded-xl tf-subsurface text-center">
              <p className="text-[10px] font-bold uppercase tf-text-muted">Hits / Misses</p>
              <p className="text-lg font-mono font-bold tf-text-primary mt-1">
                {summaryCache.hits} / {summaryCache.misses}
              </p>
            </div>
            <div className="p-3 rounded-xl tf-subsurface text-center">
              <p className="text-[10px] font-bold uppercase tf-text-muted">Entries</p>
              <p className="text-lg font-mono font-bold text-emerald-500 mt-1">
                <DatabaseZap className="w-4 h-4 inline mr-1" aria-hidden="true" />
                {summaryCache.cached_entries}
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Main Analytics Charts */}
      {chartData.length === 0 ? (
        <Card title="Live Token & Cost Analytics" subtitle="Real-time performance charting from API session logs">
          <div className="py-12 p-4 flex flex-col items-center justify-center text-center space-y-3 border-2 border-dashed rounded-xl tf-subsurface">
            <BarChart3 className="w-8 h-8 tf-text-muted" aria-hidden="true" />
            <h3 className="text-sm font-semibold tf-text-primary">No Request History Yet</h3>
            <p className="text-xs tf-text-secondary max-w-sm">
              Execute prompt compressions to populate live token reduction bar charts and cost savings curves.
            </p>
          </div>
        </Card>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
          <Card
            title="Token Reduction Per Request"
            subtitle="Original Context vs. TokenFlow Compressed Prompt"
            action={
              <span className="inline-flex items-center gap-1.5 text-xs text-emerald-500 font-semibold bg-emerald-500/10 px-2.5 py-1 rounded-lg border border-emerald-500/25">
                <TrendingUp className="w-3.5 h-3.5" aria-hidden="true" /> Live Log
              </span>
            }
          >
            <div className="h-64 sm:h-72 w-full pt-2">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.18)" vertical={false} />
                  <XAxis dataKey="name" stroke="#94a3b8" fontSize={10} tickLine={false} />
                  <YAxis stroke="#94a3b8" fontSize={10} tickLine={false} />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                  <Bar dataKey="original" name="Original Tokens" fill="#f43f5e" radius={[4, 4, 0, 0]} barSize={20} />
                  <Bar dataKey="compressed" name="Compressed Tokens" fill="#10b981" radius={[4, 4, 0, 0]} barSize={20} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <Card
            title="Cost Saved Per Request ($ USD)"
            subtitle="Calculated dynamically based on target model pricing"
            action={
              <span className="inline-flex items-center gap-1.5 text-xs text-cyan-500 font-semibold bg-cyan-500/10 px-2.5 py-1 rounded-lg border border-cyan-500/25">
                <DollarSign className="w-3.5 h-3.5" aria-hidden="true" /> USD Savings
              </span>
            }
          >
            <div className="h-64 sm:h-72 w-full pt-2">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -15, bottom: 0 }}>
                  <defs>
                    <linearGradient id="costGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#06b6d4" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.18)" vertical={false} />
                  <XAxis dataKey="name" stroke="#94a3b8" fontSize={10} tickLine={false} />
                  <YAxis stroke="#94a3b8" fontSize={10} tickLine={false} />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                  <Area
                    type="monotone"
                    dataKey="costSaved"
                    name="Cost Saved ($)"
                    stroke="#06b6d4"
                    strokeWidth={2.5}
                    fillOpacity={1}
                    fill="url(#costGradient)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </div>
      )}

      {/* Enterprise Scale-Out Monthly Savings Simulator */}
      <Card
        title="Enterprise Monthly Cost Savings Simulator"
        subtitle={`Projected savings assuming ${Math.round(avgSavedTokensPerReq)} tokens eliminated per request`}
        action={
          <div className="flex items-center gap-2">
            <Calculator className="w-4 h-4 text-emerald-500" aria-hidden="true" />
            <select
              value={monthlyRequests}
              onChange={(e) => setMonthlyRequests(Number(e.target.value))}
              aria-label="Monthly request volume"
              className="tf-input text-xs px-3 py-1.5 font-mono"
            >
              <option value={100000}>100K req / mo</option>
              <option value={500000}>500K req / mo</option>
              <option value={1000000}>1M req / mo</option>
              <option value={10000000}>10M req / mo</option>
            </select>
          </div>
        }
      >
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {PROJECTION_MODELS.map((m) => {
            const totalSavedTokens = avgSavedTokensPerReq * monthlyRequests;
            const monthlySavings = (totalSavedTokens / 1_000_000) * m.ratePer1M;
            return (
              <div key={m.id} className="p-4 rounded-xl tf-subsurface space-y-1.5">
                <p className="text-xs font-bold tf-text-primary">{m.name}</p>
                <p className="text-[11px] font-mono tf-text-muted">${m.ratePer1M}/1M input tok</p>
                <p className="text-xl font-mono font-bold text-emerald-500 pt-1">
                  ${monthlySavings.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                  <span className="text-[11px] tf-text-muted font-normal"> / mo</span>
                </p>
              </div>
            );
          })}
        </div>
      </Card>
    </div>
  );
}
