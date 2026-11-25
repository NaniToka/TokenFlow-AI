import React from 'react';
import { Zap, DollarSign, Percent, Gauge } from 'lucide-react';
import MetricCard from './MetricCard';

export default function StatsOverview({ stats, targetModel = 'gemini-1.5-flash' }) {
  const {
    total_tokens_saved = 0,
    total_cost_saved_usd = 0.0,
    avg_compression_ratio = 0.0,
    total_requests = 0,
    total_original_tokens = 0,
    total_compressed_tokens = 0,
    avg_latency_ms = 0.0,
  } = stats || {};

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
      <MetricCard
        title="Total Tokens Saved"
        value={total_tokens_saved.toLocaleString()}
        subtitle={`${total_compressed_tokens.toLocaleString()} out / ${total_original_tokens.toLocaleString()} orig`}
        icon={Zap}
        badgeText={`-${avg_compression_ratio}%`}
        badgeType="emerald"
      />

      <MetricCard
        title="Cumulative USD Saved"
        value={`$${total_cost_saved_usd.toFixed(6)}`}
        subtitle={`Model rate: ${targetModel}`}
        icon={DollarSign}
        badgeText="Input Cost"
        badgeType="cyan"
      />

      <MetricCard
        title="Compression Efficiency"
        value={`${avg_compression_ratio}%`}
        subtitle={`${total_requests} pipeline executions`}
        icon={Percent}
        badgeText="Hybrid Ranker"
        badgeType="violet"
      />

      <MetricCard
        title="Avg Pipeline Latency"
        value={`${avg_latency_ms.toFixed(1)} ms`}
        subtitle="Sub-10ms local BM25 + decay"
        icon={Gauge}
        badgeText="Live SLA"
        badgeType="emerald"
      />
    </div>
  );
}
