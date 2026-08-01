import React from 'react';
import { Zap, DollarSign, Percent, Activity } from 'lucide-react';
import MetricCard from './MetricCard';

export default function StatsOverview({ stats }) {
  const {
    total_tokens_saved = 0,
    total_cost_saved_usd = 0.0,
    avg_compression_ratio = 0.0,
    total_requests = 0,
    total_original_tokens = 0,
    total_compressed_tokens = 0
  } = stats || {};

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <MetricCard
        title="Total Tokens Saved"
        value={total_tokens_saved.toLocaleString()}
        subtitle={`${total_compressed_tokens.toLocaleString()} compressed / ${total_original_tokens.toLocaleString()} orig`}
        icon={Zap}
        badgeText={`-${avg_compression_ratio}%`}
        badgeType="emerald"
        glowColor="emerald"
      />

      <MetricCard
        title="Total Cost Saved"
        value={`$${total_cost_saved_usd.toFixed(6)}`}
        subtitle="Gemini 1.5 Flash input rates"
        icon={DollarSign}
        badgeText="USD Savings"
        badgeType="cyan"
        glowColor="cyan"
      />

      <MetricCard
        title="Avg. Compression Ratio"
        value={`${avg_compression_ratio}%`}
        subtitle="Semantic memory retention"
        icon={Percent}
        badgeText="Efficiency"
        badgeType="violet"
        glowColor="violet"
      />

      <MetricCard
        title="Total Requests"
        value={total_requests.toString()}
        subtitle="Active session requests"
        icon={Activity}
        badgeText="Live Session"
        badgeType="emerald"
        glowColor="emerald"
      />
    </div>
  );
}
