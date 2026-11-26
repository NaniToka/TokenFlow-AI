import React, { useState } from 'react';
import { FlaskConical, Target, Trophy, Play, CheckCircle2, XCircle, Sparkles } from 'lucide-react';
import Card from '../common/Card';
import ProgressRing from '../common/ProgressRing';
import { runABExperiment, runNeedleTest } from '../../services/api';

const MODES = [
  { id: 'balanced', label: 'Balanced' },
  { id: 'aggressive', label: 'Aggressive' },
  { id: 'code_preserving', label: 'Code Guard' },
  { id: 'verbatim_facts', label: 'Verbatim' },
];

export default function ExperimentsStudio({ activeHistory = [], currentQuery = '', onToast }) {
  // Variant A & B state
  const [variantA, setVariantA] = useState({
    top_k: 3,
    fusion_method: 'linear',
    compression_mode: 'balanced',
    use_mmr: false,
    use_reranker: false,
  });
  const [variantB, setVariantB] = useState({
    top_k: 3,
    fusion_method: 'rrf',
    compression_mode: 'code_preserving',
    use_mmr: true,
    use_reranker: true,
  });
  const [abResult, setAbResult] = useState(null);
  const [isRunningAb, setIsRunningAb] = useState(false);

  // Needle-in-a-Haystack state
  const [haystackTurns, setHaystackTurns] = useState(24);
  const [needleDepthPct, setNeedleDepthPct] = useState(30);
  const [needleTopK, setNeedleTopK] = useState(3);
  const [needleFusion, setNeedleFusion] = useState('rrf');
  const [needleResult, setNeedleResult] = useState(null);
  const [isRunningNeedle, setIsRunningNeedle] = useState(false);

  const handleRunAB = async (e) => {
    e.preventDefault();
    if (!activeHistory.length || !currentQuery.trim()) {
      onToast?.('Load a conversation preset first to run an A/B comparison.', 'warning');
      return;
    }
    setIsRunningAb(true);
    try {
      const res = await runABExperiment({
        history: activeHistory,
        current_message: currentQuery,
        variant_a: variantA,
        variant_b: variantB,
      });
      setAbResult(res);
      onToast?.(`A/B Complete: ${res.winner} achieved higher composite utility.`);
    } catch (err) {
      onToast?.(err.response?.data?.detail || 'A/B experiment failed.', 'error');
    } finally {
      setIsRunningAb(false);
    }
  };

  const handleRunNeedle = async (e) => {
    e.preventDefault();
    setIsRunningNeedle(true);
    try {
      const res = await runNeedleTest({
        haystack_turns: Number(haystackTurns),
        needle_depth_pct: Number(needleDepthPct),
        top_k: Number(needleTopK),
        fusion_method: needleFusion,
        compression_mode: 'balanced',
      });
      setNeedleResult(res);
      onToast?.(
        res.needle_retained
          ? `Needle ${res.needle_code} retained via ${res.retained_via}!`
          : `Needle ${res.needle_code} evicted at ${res.needle_depth_pct}% depth.`,
        res.needle_retained ? 'success' : 'warning'
      );
    } catch (err) {
      onToast?.(err.response?.data?.detail || 'Needle stress test failed.', 'error');
    } finally {
      setIsRunningNeedle(false);
    }
  };

  const renderVariantConfig = (label, cfg, setCfg, accentClass) => (
    <fieldset className="p-4 rounded-xl tf-subsurface space-y-3">
      <legend className={`px-2 text-xs font-extrabold uppercase tracking-wider ${accentClass}`}>
        {label}
      </legend>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <span className="block text-[10px] font-bold uppercase tf-text-muted mb-1.5">Rank Fusion</span>
          <div className="flex gap-2">
            {['linear', 'rrf'].map((method) => (
              <label
                key={method}
                className={`flex-1 flex items-center justify-center gap-1.5 px-2.5 py-1.5 rounded-lg border text-[11px] font-mono font-bold cursor-pointer ${
                  cfg.fusion_method === method
                    ? 'bg-emerald-500/15 border-emerald-500/40 text-emerald-500'
                    : 'tf-card tf-text-secondary'
                }`}
              >
                <input
                  type="radio"
                  name={`${label}-fusion`}
                  value={method}
                  checked={cfg.fusion_method === method}
                  onChange={() => setCfg({ ...cfg, fusion_method: method })}
                  className="sr-only"
                />
                <span>{method.toUpperCase()}</span>
              </label>
            ))}
          </div>
        </div>

        <div>
          <label htmlFor={`${label}-mode`} className="block text-[10px] font-bold uppercase tf-text-muted mb-1.5">
            Mode Profile
          </label>
          <select
            id={`${label}-mode`}
            value={cfg.compression_mode}
            onChange={(e) => setCfg({ ...cfg, compression_mode: e.target.value })}
            className="tf-input w-full px-2.5 py-1.5 text-xs font-medium"
          >
            {MODES.map((m) => (
              <option key={m.id} value={m.id}>{m.label}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
        <label className="flex items-center gap-2 text-xs font-medium tf-text-primary cursor-pointer">
          <input
            type="checkbox"
            switch=""
            checked={cfg.use_mmr}
            onChange={(e) => setCfg({ ...cfg, use_mmr: e.target.checked })}
            className="tf-switch"
          />
          <span>MMR Diversity</span>
        </label>

        <label className="flex items-center gap-2 text-xs font-medium tf-text-primary cursor-pointer">
          <input
            type="checkbox"
            switch=""
            checked={cfg.use_reranker}
            onChange={(e) => setCfg({ ...cfg, use_reranker: e.target.checked })}
            className="tf-switch"
          />
          <span>N-gram Reranker</span>
        </label>

        <label className="flex items-center gap-2 text-xs font-mono tf-text-secondary">
          <span>K=</span>
          <input
            type="number"
            min="1"
            max="10"
            value={cfg.top_k}
            onChange={(e) => setCfg({ ...cfg, top_k: Math.max(1, Math.min(10, Number(e.target.value) || 3)) })}
            className="tf-input w-14 px-2 py-1 text-xs text-center font-bold"
          />
        </label>
      </div>
    </fieldset>
  );

  return (
    <div className="space-y-6">
      {/* 1. A/B Strategy Experiment Comparator */}
      <Card
        title="A/B Strategy Experiment Bench"
        subtitle="Benchmark two compression & retrieval pipelines side-by-side on identical multi-turn context"
      >
        <form onSubmit={handleRunAB} className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {renderVariantConfig('Variant A (Baseline)', variantA, setVariantA, 'text-cyan-500')}
            {renderVariantConfig('Variant B (Candidate)', variantB, setVariantB, 'text-violet-500')}
          </div>

          <div className="flex flex-wrap items-center justify-between gap-3 p-3.5 rounded-xl tf-subsurface">
            <div className="text-xs tf-text-secondary truncate max-w-2xl">
              <strong className="tf-text-primary">Active Query:</strong> {currentQuery || 'None selected'} ({activeHistory.length} turns)
            </div>
            <button
              type="submit"
              disabled={isRunningAb}
              className="tf-btn-target flex items-center gap-2 px-5 py-2 rounded-xl bg-gradient-to-r from-emerald-500 to-cyan-500 text-zinc-950 font-bold text-xs shadow-md cursor-pointer disabled:opacity-50"
            >
              <FlaskConical className={`w-4 h-4 ${isRunningAb ? 'animate-spin' : ''}`} aria-hidden="true" />
              <span>{isRunningAb ? 'Running Evaluation...' : 'Execute A/B Benchmark'}</span>
            </button>
          </div>
        </form>

        {abResult && (
          <div className="mt-5 pt-5 space-y-4" style={{ borderTop: '1px solid var(--border-subtle)' }}>
            <div className="flex flex-wrap items-center justify-between gap-3 p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/35">
              <div className="flex items-center gap-2.5">
                <Trophy className="w-5 h-5 text-emerald-500 shrink-0" aria-hidden="true" />
                <div>
                  <p className="text-xs font-extrabold text-emerald-500 uppercase tracking-wider">
                    Empirical Winner: {abResult.winner}
                  </p>
                  <p className="text-[11px] tf-text-secondary">
                    Scored by composite utility (60% semantic fidelity + 40% token reduction)
                  </p>
                </div>
              </div>
              <div className="flex flex-wrap gap-2 font-mono text-[11px]">
                <span className="px-2.5 py-1 rounded-lg tf-card tf-text-primary">
                  Δ Saved: <strong>{abResult.delta.tokens_saved_diff >= 0 ? '+' : ''}{abResult.delta.tokens_saved_diff} tok</strong>
                </span>
                <span className="px-2.5 py-1 rounded-lg tf-card tf-text-primary">
                  Δ Fidelity: <strong>{abResult.delta.fidelity_diff >= 0 ? '+' : ''}{abResult.delta.fidelity_diff}%</strong>
                </span>
                <span className="px-2.5 py-1 rounded-lg tf-card tf-text-primary">
                  Δ Latency: <strong>{abResult.delta.latency_diff_ms >= 0 ? '+' : ''}{abResult.delta.latency_diff_ms}ms</strong>
                </span>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[
                { name: 'Variant A', data: abResult.variant_a, color: 'var(--accent-secondary)' },
                { name: 'Variant B', data: abResult.variant_b, color: 'var(--accent-tertiary)' },
              ].map((v) => (
                <div key={v.name} className="p-4 rounded-xl tf-subsurface flex items-center justify-between gap-4">
                  <div className="space-y-1.5 min-w-0">
                    <div className="flex items-center gap-2">
                      <h3 className="text-xs font-extrabold tf-text-primary">{v.name}</h3>
                      <span className="px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-500 font-mono text-[10px] font-bold">
                        Grade {v.data.composite_grade}
                      </span>
                    </div>
                    <p className="text-[11px] font-mono tf-text-muted truncate">{v.data.strategy}</p>
                    <p className="text-xs font-mono tf-text-secondary">
                      Saved <strong>{v.data.tokens_saved}</strong> tok • {v.data.latency_ms}ms
                    </p>
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    <ProgressRing
                      value={v.data.compression_ratio}
                      label={`${v.name} token reduction`}
                      displayValue={`${Math.round(v.data.compression_ratio)}%`}
                      subLabel="Ratio"
                      size={74}
                      thickness={7}
                      color={v.color}
                    />
                    <ProgressRing
                      value={v.data.semantic_fidelity}
                      label={`${v.name} semantic fidelity`}
                      displayValue={`${Math.round(v.data.semantic_fidelity)}%`}
                      subLabel="Fidelity"
                      size={74}
                      thickness={7}
                      color="var(--accent-primary)"
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </Card>

      {/* 2. Needle-in-a-Haystack Stress Lab */}
      <Card
        title="Needle-in-a-Haystack Retrieval Stress Test"
        subtitle="Inject a secret production token (`TF-NEEDLE-8492`) at arbitrary dialogue depth to benchmark recall under drift noise"
      >
        <form onSubmit={handleRunNeedle} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 p-4 rounded-xl tf-subsurface">
            <label className="block text-xs tf-text-secondary">
              <span className="font-bold block mb-1">
                Haystack Depth: <strong className="font-mono text-emerald-500">{haystackTurns} turns</strong>
              </span>
              <input
                type="range"
                min="4"
                max="60"
                step="2"
                value={haystackTurns}
                onChange={(e) => setHaystackTurns(Number(e.target.value))}
                style={{ '--attr-min': 4, '--attr-max': 60, '--control-value': haystackTurns }}
                className="tf-slider"
              />
            </label>

            <label className="block text-xs tf-text-secondary">
              <span className="font-bold block mb-1">
                Needle Depth Position: <strong className="font-mono text-cyan-500">{needleDepthPct}%</strong>
              </span>
              <input
                type="range"
                min="0"
                max="100"
                step="5"
                value={needleDepthPct}
                onChange={(e) => setNeedleDepthPct(Number(e.target.value))}
                style={{ '--attr-min': 0, '--attr-max': 100, '--control-value': needleDepthPct }}
                className="tf-slider"
              />
            </label>

            <label className="block text-xs tf-text-secondary">
              <span className="font-bold block mb-1">
                Top-K Window: <strong className="font-mono text-violet-500">{needleTopK}</strong>
              </span>
              <input
                type="range"
                min="1"
                max="10"
                value={needleTopK}
                onChange={(e) => setNeedleTopK(Number(e.target.value))}
                style={{ '--attr-min': 1, '--attr-max': 10, '--control-value': needleTopK }}
                className="tf-slider"
              />
            </label>

            <div>
              <span className="block text-[10px] font-bold uppercase tf-text-muted mb-1.5">Fusion Algorithm</span>
              <div className="flex gap-2">
                {['rrf', 'linear'].map((f) => (
                  <label
                    key={f}
                    className={`flex-1 flex items-center justify-center gap-1 px-2.5 py-2 rounded-lg border text-xs font-mono font-bold cursor-pointer ${
                      needleFusion === f
                        ? 'bg-emerald-500/15 border-emerald-500/40 text-emerald-500'
                        : 'tf-card tf-text-secondary'
                    }`}
                  >
                    <input
                      type="radio"
                      name="needle-fusion"
                      value={f}
                      checked={needleFusion === f}
                      onChange={() => setNeedleFusion(f)}
                      className="sr-only"
                    />
                    <span>{f.toUpperCase()}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={isRunningNeedle}
              className="tf-btn-target flex items-center gap-2 px-5 py-2 rounded-xl bg-gradient-to-r from-violet-500 to-cyan-500 text-white font-bold text-xs shadow-md cursor-pointer disabled:opacity-50"
            >
              <Target className={`w-4 h-4 ${isRunningNeedle ? 'animate-spin' : ''}`} aria-hidden="true" />
              <span>{isRunningNeedle ? 'Injecting & Probing...' : 'Run Needle Stress Test'}</span>
            </button>
          </div>
        </form>

        {needleResult && (
          <div className="mt-5 p-4 rounded-xl tf-subsurface flex flex-col sm:flex-row items-center justify-between gap-4 border border-emerald-500/25">
            <div className="flex items-start gap-3">
              {needleResult.needle_retained ? (
                <CheckCircle2 className="w-6 h-6 text-emerald-500 shrink-0 mt-0.5" aria-hidden="true" />
              ) : (
                <XCircle className="w-6 h-6 text-rose-500 shrink-0 mt-0.5" aria-hidden="true" />
              )}
              <div className="space-y-1">
                <p className="text-xs font-extrabold tf-text-primary flex items-center gap-2">
                  <span>Needle {needleResult.needle_code}:</span>
                  <span className={needleResult.needle_retained ? 'text-emerald-500' : 'text-rose-500'}>
                    {needleResult.needle_retained ? 'RETAINED' : 'EVICTED'}
                  </span>
                </p>
                <p className="text-xs font-mono tf-text-secondary">
                  Placed at Turn #{needleResult.needle_turn_index} / {needleResult.haystack_turns} ({needleResult.needle_depth_pct}% depth) • Surfaced via <strong>{needleResult.retained_via}</strong>
                </p>
                <p className="text-[11px] font-mono tf-text-muted">
                  <Play className="w-3 h-3 inline mr-1" aria-hidden="true" />
                  {needleResult.original_tokens} → {needleResult.compressed_tokens} tok ({needleResult.latency_ms}ms) • {needleResult.ranking_strategy}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3 shrink-0">
              <ProgressRing
                value={needleResult.compression_ratio}
                label="Needle stress test compression ratio"
                displayValue={`${Math.round(needleResult.compression_ratio)}%`}
                subLabel="Saved"
                size={80}
                thickness={8}
                color={needleResult.needle_retained ? 'var(--accent-primary)' : '#f43f5e'}
              />
              <Sparkles className="w-4 h-4 text-emerald-500 hidden sm:block" aria-hidden="true" />
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}
