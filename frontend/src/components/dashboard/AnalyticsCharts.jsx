import React from 'react';
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
  Legend
} from 'recharts';
import Card from '../common/Card';
import { BarChart3, TrendingUp, DollarSign } from 'lucide-react';

export default function AnalyticsCharts({ stats }) {
  const requestHistory = stats?.request_history || [];

  const chartData = requestHistory.map((item, index) => ({
    name: `Req #${item.id || index + 1}`,
    original: item.original_tokens || 0,
    compressed: item.compressed_tokens || 0,
    tokensSaved: item.tokens_saved || 0,
    costSaved: item.cost_saved_usd || 0,
    ratio: item.compression_ratio || 0,
  }));

  if (chartData.length === 0) {
    return (
      <Card title="Live Analytics & Token Reduction Trends" subtitle="Real-time performance charting from API session logs">
        <div className="py-12 sm:py-16 p-4 flex flex-col items-center justify-center text-center space-y-3 border-2 border-dashed border-zinc-800 rounded-xl bg-zinc-950/40">
          <div className="w-12 h-12 rounded-2xl bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-500">
            <BarChart3 className="w-6 h-6" />
          </div>
          <h4 className="text-sm sm:text-base font-semibold text-zinc-300">No Analytics History Yet</h4>
          <p className="text-xs text-zinc-500 max-w-sm">
            Execute compression requests to generate real-time token reduction charts and cumulative cost savings trends.
          </p>
        </div>
      </Card>
    );
  }

  // Custom Dark Mode Tooltip
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-zinc-900 border border-zinc-700 p-3 rounded-xl shadow-xl text-xs space-y-1.5 z-50">
          <p className="font-bold text-zinc-200 border-b border-zinc-800 pb-1">{label}</p>
          {payload.map((entry, index) => (
            <div key={index} className="flex items-center justify-between gap-4">
              <span className="font-medium" style={{ color: entry.color }}>
                {entry.name}:
              </span>
              <span className="font-bold text-zinc-100">
                {typeof entry.value === 'number' && entry.value < 1
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
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6 min-w-0">
      {/* Chart 1: Token Reduction Comparison */}
      <Card
        title="Token Reduction Per Request"
        subtitle="Original Context vs. TokenFlow Compressed Prompt"
        action={
          <div className="flex items-center gap-1.5 text-xs text-emerald-400 font-semibold bg-emerald-500/10 px-2.5 py-1 rounded-lg border border-emerald-500/20">
            <TrendingUp className="w-3.5 h-3.5" /> Live Log
          </div>
        }
      >
        <div className="h-64 sm:h-72 w-full pt-4 min-w-0">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
              <XAxis dataKey="name" stroke="#71717a" fontSize={10} tickLine={false} />
              <YAxis stroke="#71717a" fontSize={10} tickLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
              <Bar dataKey="original" name="Original Tokens" fill="#f43f5e" radius={[4, 4, 0, 0]} barSize={20} />
              <Bar dataKey="compressed" name="Compressed Tokens" fill="#10b981" radius={[4, 4, 0, 0]} barSize={20} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>

      {/* Chart 2: Cost Saved Trend */}
      <Card
        title="Cumulative Cost Saved ($ USD)"
        subtitle="Saved input tokens calculated using Gemini Flash rates"
        action={
          <div className="flex items-center gap-1.5 text-xs text-cyan-400 font-semibold bg-cyan-500/10 px-2.5 py-1 rounded-lg border border-cyan-500/20">
            <DollarSign className="w-3.5 h-3.5" /> USD Analytics
          </div>
        }
      >
        <div className="h-64 sm:h-72 w-full pt-4 min-w-0">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
              <defs>
                <linearGradient id="costGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#06b6d4" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
              <XAxis dataKey="name" stroke="#71717a" fontSize={10} tickLine={false} />
              <YAxis stroke="#71717a" fontSize={10} tickLine={false} />
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
  );
}
