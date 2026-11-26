import React, { useState } from 'react';
import {
  Sparkles,
  MessageSquare,
  Search,
  Filter,
  Shield,
  Cpu,
  SlidersHorizontal,
  Zap,
  Layers,
  GitMerge,
  Gauge,
} from 'lucide-react';
import { DEMO_PRESETS } from '../../data/demoConversation';
import Card from '../common/Card';

const MODEL_OPTIONS = [
  { id: 'gemini-1.5-flash', label: 'Gemini 1.5 Flash ($0.075/1M)' },
  { id: 'gemini-2.0-flash', label: 'Gemini 2.0 Flash ($0.10/1M)' },
  { id: 'gemini-1.5-pro', label: 'Gemini 1.5 Pro ($1.25/1M)' },
  { id: 'gpt-4o-mini', label: 'GPT-4o Mini ($0.15/1M)' },
  { id: 'gpt-4o', label: 'GPT-4o ($2.50/1M)' },
  { id: 'claude-3-5-sonnet', label: 'Claude 3.5 Sonnet ($3.00/1M)' },
];

const MODE_OPTIONS = [
  { id: 'balanced', label: 'Balanced' },
  { id: 'aggressive', label: 'Aggressive' },
  { id: 'code_preserving', label: 'Code Guard' },
  { id: 'verbatim_facts', label: 'Verbatim' },
];

const FUSION_OPTIONS = [
  { id: 'linear', label: 'Linear Blend', hint: 'Weighted sum' },
  { id: 'rrf', label: 'RRF Fusion', hint: 'Rank reciprocal' },
];

export default function DemoModeSelector({
  selectedPresetId,
  onSelectPreset,
  topK,
  onTopKChange,
  targetModel,
  onTargetModelChange,
  compressionMode,
  onCompressionModeChange,
  fusionMethod,
  onFusionMethodChange,
  useMmr,
  onUseMmrChange,
  useReranker,
  onUseRerankerChange,
  useDedup,
  onUseDedupChange,
  maxContextTokens,
  onMaxContextTokensChange,
  alphaOverride,
  onAlphaOverrideChange,
  sanitizePii,
  onSanitizePiiChange,
  useCache,
  onUseCacheChange,
  onRunCompression,
  isCompressing,
}) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedDomain, setSelectedDomain] = useState('All');

  const currentPreset = DEMO_PRESETS.find((p) => p.id === selectedPresetId) || DEMO_PRESETS[0];
  const domains = ['All', ...new Set(DEMO_PRESETS.map((p) => p.domain))];

  const filteredPresets = DEMO_PRESETS.filter((preset) => {
    const matchesDomain = selectedDomain === 'All' || preset.domain === selectedDomain;
    const matchesSearch =
      preset.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      preset.domain.toLowerCase().includes(searchQuery.toLowerCase()) ||
      preset.description.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesDomain && matchesSearch;
  });

  const alphaValue = alphaOverride === null ? 0.7 : alphaOverride;

  return (
    <Card
      title="Strategy Controls & Multi-Turn Benchmark Scenarios"
      subtitle="Configure RRF vs Linear fusion, MMR diversity, cross-encoder reranking, knapsack token budget, and 21+ enterprise workloads"
      action={
        <div className="flex flex-wrap items-center gap-3">
          <label className="flex items-center gap-2 text-xs tf-text-secondary font-medium">
            <span>Top-K Turns:</span>
            <input
              type="range"
              min="1"
              max="10"
              value={topK}
              aria-label="Top-K retained turns"
              onChange={(e) => onTopKChange(Number(e.target.value))}
              style={{ '--attr-min': 1, '--attr-max': 10, '--control-value': topK }}
              className="tf-slider w-24"
            />
            <span className="font-mono font-bold text-emerald-500 w-5 text-center">{topK}</span>
          </label>
        </div>
      }
    >
      <div className="space-y-5">
        {/* Primary Hyperparameter & Radio Strategy Strip */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-3.5 p-3.5 rounded-xl tf-subsurface">
          {/* Target LLM (6+ options -> native <select> per forms matrix) */}
          <div className="lg:col-span-3">
            <label htmlFor="target-model-select" className="block text-[10px] font-bold uppercase tracking-wider tf-text-muted mb-1.5">
              <Cpu className="w-3 h-3 inline mr-1" aria-hidden="true" />
              Target LLM Pricing
            </label>
            <select
              id="target-model-select"
              value={targetModel}
              onChange={(e) => onTargetModelChange(e.target.value)}
              className="tf-input w-full px-2.5 py-2 text-xs font-medium"
            >
              {MODEL_OPTIONS.map((m) => (
                <option key={m.id} value={m.id}>{m.label}</option>
              ))}
            </select>

            {/* Alpha Slider */}
            <div className="mt-3">
              <div className="flex items-center justify-between mb-1">
                <label htmlFor="alpha-slider" className="text-[10px] font-bold uppercase tracking-wider tf-text-muted">
                  Dense vs BM25 (α)
                </label>
                <button
                  type="button"
                  onClick={() => onAlphaOverrideChange(alphaOverride === null ? 0.7 : null)}
                  className="text-[10px] font-mono font-bold text-emerald-500 hover:underline cursor-pointer"
                >
                  {alphaOverride === null ? 'Auto-Tuned' : `Manual ${alphaValue.toFixed(2)} (Reset)`}
                </button>
              </div>
              <input
                id="alpha-slider"
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={alphaValue}
                onChange={(e) => onAlphaOverrideChange(parseFloat(e.target.value))}
                style={{ '--attr-min': 0, '--attr-max': 1, '--control-value': alphaValue }}
                className="tf-slider"
              />
            </div>
          </div>

          {/* Visible Radio Group: Compression Mode (4 exclusive options) */}
          <fieldset className="lg:col-span-5 min-w-0">
            <legend className="text-[10px] font-bold uppercase tracking-wider tf-text-muted mb-1.5 flex items-center gap-1">
              <SlidersHorizontal className="w-3 h-3" aria-hidden="true" />
              Compression Profile
            </legend>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-1.5">
              {MODE_OPTIONS.map((m) => {
                const active = compressionMode === m.id;
                return (
                  <label
                    key={m.id}
                    className={`flex items-center justify-center px-2 py-2 rounded-lg border text-[11px] font-semibold text-center cursor-pointer transition-all ${
                      active
                        ? 'bg-emerald-500/15 border-emerald-500/45 text-emerald-500'
                        : 'tf-card tf-text-secondary hover:border-emerald-500/30'
                    }`}
                  >
                    <input
                      type="radio"
                      name="compression_mode"
                      value={m.id}
                      checked={active}
                      onChange={() => onCompressionModeChange(m.id)}
                      className="sr-only"
                    />
                    <span className="truncate">{m.label}</span>
                  </label>
                );
              })}
            </div>

            {/* Knapsack Max Token Budget Control */}
            <div className="mt-3 p-2.5 rounded-lg tf-card">
              <div className="flex items-center justify-between text-[10px] font-bold uppercase tracking-wider mb-1">
                <label htmlFor="budget-slider" className="tf-text-muted flex items-center gap-1">
                  <Gauge className="w-3 h-3 text-cyan-500" aria-hidden="true" />
                  Hard Token Budget Cap
                </label>
                <div className="flex items-center gap-2 font-mono">
                  <span className={maxContextTokens ? 'text-cyan-500 font-extrabold' : 'tf-text-muted'}>
                    {maxContextTokens ? `${maxContextTokens} tok` : 'Unbounded'}
                  </span>
                  <button
                    type="button"
                    onClick={() => onMaxContextTokensChange(maxContextTokens ? null : 256)}
                    className="text-emerald-500 hover:underline cursor-pointer"
                  >
                    {maxContextTokens ? 'Disable' : 'Enable Cap'}
                  </button>
                </div>
              </div>
              {maxContextTokens !== null && (
                <input
                  id="budget-slider"
                  type="range"
                  min="96"
                  max="1024"
                  step="32"
                  value={maxContextTokens}
                  onChange={(e) => onMaxContextTokensChange(Number(e.target.value))}
                  style={{ '--attr-min': 96, '--attr-max': 1024, '--control-value': maxContextTokens }}
                  className="tf-slider"
                />
              )}
            </div>
          </fieldset>

          {/* Visible Radio Group: Fusion Method + Switch Controls */}
          <div className="lg:col-span-4 flex flex-col justify-between gap-2.5">
            <fieldset>
              <legend className="text-[10px] font-bold uppercase tracking-wider tf-text-muted mb-1.5 flex items-center gap-1">
                <GitMerge className="w-3 h-3" aria-hidden="true" />
                Rank Fusion Algorithm
              </legend>
              <div className="grid grid-cols-2 gap-1.5">
                {FUSION_OPTIONS.map((f) => {
                  const active = fusionMethod === f.id;
                  return (
                    <label
                      key={f.id}
                      className={`flex items-center justify-center gap-1.5 px-2.5 py-2 rounded-lg border text-[11px] font-semibold cursor-pointer transition-all ${
                        active
                          ? 'bg-cyan-500/15 border-cyan-500/45 text-cyan-500'
                          : 'tf-card tf-text-secondary hover:border-cyan-500/30'
                      }`}
                    >
                      <input
                        type="radio"
                        name="fusion_method"
                        value={f.id}
                        checked={active}
                        onChange={() => onFusionMethodChange(f.id)}
                        className="sr-only"
                      />
                      <span>{f.label}</span>
                    </label>
                  );
                })}
              </div>
            </fieldset>

            <div className="grid grid-cols-2 gap-x-3 gap-y-2 pt-1">
              <label className="flex items-center gap-2 text-[11px] font-medium tf-text-primary cursor-pointer">
                <input
                  type="checkbox"
                  switch=""
                  checked={useMmr}
                  onChange={(e) => onUseMmrChange(e.target.checked)}
                  className="tf-switch"
                />
                <span>MMR Diversity</span>
              </label>

              <label className="flex items-center gap-2 text-[11px] font-medium tf-text-primary cursor-pointer">
                <input
                  type="checkbox"
                  switch=""
                  checked={useReranker}
                  onChange={(e) => onUseRerankerChange(e.target.checked)}
                  className="tf-switch"
                />
                <Layers className="w-3 h-3 text-violet-500 shrink-0" aria-hidden="true" />
                <span>Reranker</span>
              </label>

              <label className="flex items-center gap-2 text-[11px] font-medium tf-text-primary cursor-pointer">
                <input
                  type="checkbox"
                  switch=""
                  checked={useDedup}
                  onChange={(e) => onUseDedupChange(e.target.checked)}
                  className="tf-switch"
                />
                <span>Dedup Retries</span>
              </label>

              <label className="flex items-center gap-2 text-[11px] font-medium tf-text-primary cursor-pointer">
                <input
                  type="checkbox"
                  switch=""
                  checked={sanitizePii}
                  onChange={(e) => onSanitizePiiChange(e.target.checked)}
                  className="tf-switch"
                />
                <Shield className="w-3 h-3 text-amber-500 shrink-0" aria-hidden="true" />
                <span>Redact PII</span>
              </label>

              <label className="flex items-center gap-2 text-[11px] font-medium tf-text-primary cursor-pointer col-span-2">
                <input
                  type="checkbox"
                  switch=""
                  checked={useCache}
                  onChange={(e) => onUseCacheChange(e.target.checked)}
                  className="tf-switch"
                />
                <Zap className="w-3 h-3 text-cyan-500 shrink-0" aria-hidden="true" />
                <span>Semantic LRU Cache</span>
              </label>
            </div>
          </div>
        </div>

        {/* Semantic <search> Container for Scenario Filter Bar */}
        <search className="flex flex-col sm:flex-row items-center justify-between gap-3 p-3 rounded-xl tf-subsurface">
          <div className="relative w-full sm:w-80">
            <Search className="w-4 h-4 tf-text-muted absolute left-3 top-2.5" aria-hidden="true" />
            <input
              type="search"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search scenarios by domain, stack, or keyword..."
              aria-label="Search scenarios"
              className="tf-input pl-9 pr-3 py-1.5 text-xs w-full"
            />
          </div>

          <div className="flex items-center gap-2 w-full sm:w-auto">
            <Filter className="w-3.5 h-3.5 tf-text-muted shrink-0" aria-hidden="true" />
            <select
              value={selectedDomain}
              onChange={(e) => setSelectedDomain(e.target.value)}
              aria-label="Filter scenarios by domain"
              className="tf-input text-xs px-3 py-1.5"
            >
              {domains.map((domain) => (
                <option key={domain} value={domain}>{domain}</option>
              ))}
            </select>
            <span className="text-[11px] font-mono tf-text-muted shrink-0">
              ({filteredPresets.length})
            </span>
          </div>
        </search>

        {/* Preset Selector Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 max-h-[360px] overflow-y-auto tf-scroller pr-1">
          {filteredPresets.map((preset) => {
            const isSelected = preset.id === currentPreset.id;
            return (
              <button
                key={preset.id}
                type="button"
                onClick={() => onSelectPreset(preset.id)}
                className={`p-3.5 rounded-xl border text-left transition-all flex flex-col justify-between cursor-pointer ${
                  isSelected
                    ? 'bg-emerald-500/10 border-emerald-500/50 shadow-sm'
                    : 'tf-subsurface hover:border-emerald-500/30'
                }`}
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-1.5">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-500 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20 truncate">
                      {preset.domain}
                    </span>
                    <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded tf-card tf-text-secondary shrink-0">
                      {preset.history.length} turns
                    </span>
                  </div>

                  <h3 className={`text-xs font-bold mb-1 ${isSelected ? 'text-emerald-500' : 'tf-text-primary'}`}>
                    {preset.title}
                  </h3>
                  <p className="text-[11px] tf-text-secondary leading-relaxed mb-2.5 line-clamp-2">
                    {preset.description}
                  </p>
                </div>

                <div
                  className="flex items-center justify-between text-[10px] font-mono pt-2 mt-auto w-full gap-2"
                  style={{ borderTop: '1px solid var(--border-subtle)' }}
                >
                  <span className="truncate tf-text-muted">Q: {preset.current_message}</span>
                  <span className={`shrink-0 font-bold ${isSelected ? 'text-emerald-500' : 'tf-text-muted'}`}>
                    {isSelected ? '✓ Active' : 'Load'}
                  </span>
                </div>
              </button>
            );
          })}
        </div>

        {/* Action Footer */}
        <div className="p-4 rounded-xl tf-subsurface flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/25 flex items-center justify-center text-emerald-500 shrink-0">
              <MessageSquare className="w-5 h-5" aria-hidden="true" />
            </div>
            <div className="min-w-0">
              <p className="text-xs font-bold tf-text-primary flex flex-wrap items-center gap-2">
                <span>{currentPreset.title}</span>
                <span className="text-[10px] text-emerald-500 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/25">
                  {currentPreset.domain}
                </span>
              </p>
              <p className="text-[11px] tf-text-secondary truncate">
                {currentPreset.history.length} turns • Target: <strong className="font-mono">{targetModel}</strong> • Fusion: <strong className="font-mono">{fusionMethod.toUpperCase()}</strong>
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onRunCompression}
            disabled={isCompressing}
            className="tf-btn-target w-full sm:w-auto flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-400 hover:to-cyan-400 text-zinc-950 font-bold text-xs shadow-lg shadow-emerald-500/20 transition-all active:scale-95 disabled:opacity-50 shrink-0 cursor-pointer"
          >
            <Sparkles className={`w-4 h-4 ${isCompressing ? 'animate-spin' : ''}`} aria-hidden="true" />
            <span>{isCompressing ? 'Optimizing Context...' : 'Run TokenFlow Pipeline'}</span>
          </button>
        </div>
      </div>
    </Card>
  );
}
