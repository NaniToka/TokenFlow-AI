import React, { useState } from 'react';
import { FlaskConical, Award, CheckCircle2, Play, Sparkles } from 'lucide-react';
import Card from '../common/Card';
import { evaluateCompression, inspectRanking } from '../../services/api';

export default function QualityEvaluator({
  activeHistory,
  currentQuery,
  compressionResult,
  onToast,
}) {
  const [evalReport, setEvalReport] = useState(null);
  const [ablationResults, setAblationResults] = useState([]);
  const [isEvaluating, setIsEvaluating] = useState(false);

  const handleRunEvaluation = async () => {
    if (!compressionResult) {
      onToast?.('Run a prompt compression first to evaluate its fidelity.', 'error');
      return;
    }
    setIsEvaluating(true);
    try {
      const report = await evaluateCompression(activeHistory, compressionResult);
      setEvalReport(report);
      onToast?.(`Quality Evaluation complete: Grade ${report.composite_grade}`);
    } catch {
      onToast?.('Failed to run quality evaluation.', 'error');
    } finally {
      setIsEvaluating(false);
    }
  };

  const handleRunAblation = async () => {
    if (!activeHistory.length || !currentQuery.trim()) return;
    setIsEvaluating(true);
    try {
      const modes = ['balanced', 'aggressive', 'code_preserving', 'verbatim_facts'];
      const comparisons = await Promise.all(
        modes.map(async (mode) => {
          const res = await inspectRanking({
            history: activeHistory,
            current_message: currentQuery,
            top_k: 3,
            compression_mode: mode,
          });
          return { mode, ...res };
        })
      );
      setAblationResults(comparisons);
      onToast?.('Completed 4-strategy ablation comparison.');
    } catch {
      onToast?.('Failed to execute strategy ablation.', 'error');
    } finally {
      setIsEvaluating(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card
        title="LLM-as-Judge Context Quality & Fidelity Evaluator"
        subtitle="Quantifies factual recall, technical entity preservation, hallucination risk, and ranking strategy ablation"
        action={
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={handleRunAblation}
              disabled={isEvaluating}
              className="tf-btn-target flex items-center gap-1.5 px-3.5 py-2 rounded-xl tf-subsurface tf-text-primary text-xs font-semibold hover:border-emerald-500/40 cursor-pointer disabled:opacity-50"
            >
              <Play className="w-3.5 h-3.5 text-cyan-500" aria-hidden="true" />
              <span>Run 4-Mode Ablation</span>
            </button>

            <button
              type="button"
              onClick={handleRunEvaluation}
              disabled={isEvaluating || !compressionResult}
              className="tf-btn-target flex items-center gap-1.5 px-4 py-2 rounded-xl bg-gradient-to-r from-emerald-500 to-cyan-500 text-zinc-950 font-bold text-xs cursor-pointer disabled:opacity-50"
            >
              <FlaskConical className="w-3.5 h-3.5" aria-hidden="true" />
              <span>{isEvaluating ? 'Evaluating...' : 'Evaluate Last Compression'}</span>
            </button>
          </div>
        }
      >
        {evalReport ? (
          <div className="space-y-5">
            {/* Grade Banner */}
            <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="w-11 h-11 rounded-xl bg-emerald-500/20 flex items-center justify-center text-emerald-500 shrink-0">
                  <Award className="w-6 h-6" aria-hidden="true" />
                </div>
                <div>
                  <p className="text-[11px] font-mono uppercase font-bold text-emerald-500">
                    Composite Quality Grade
                  </p>
                  <p className="text-lg font-bold tf-text-primary">{evalReport.composite_grade}</p>
                </div>
              </div>
              <div className="text-xs font-mono tf-text-secondary">
                {evalReport.original_tokens} → {evalReport.compressed_tokens} tokens ({evalReport.compression_ratio}% saved)
              </div>
            </div>

            {/* 4 Scorecard Bars */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {[
                { label: 'Lexical Fact Recall', val: evalReport.lexical_recall, color: 'bg-emerald-500', goodHigh: true },
                { label: 'Entity Coverage', val: evalReport.entity_coverage, color: 'bg-cyan-500', goodHigh: true },
                { label: 'Semantic Fidelity', val: evalReport.semantic_fidelity, color: 'bg-violet-500', goodHigh: true },
                { label: 'Hallucination Risk', val: evalReport.hallucination_risk, color: 'bg-amber-500', goodHigh: false },
              ].map((m) => (
                <div key={m.label} className="p-3.5 rounded-xl tf-subsurface space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold tf-text-secondary">{m.label}</span>
                    <span className="font-mono font-bold tf-text-primary">{m.val}%</span>
                  </div>
                  <div className="w-full h-2 rounded-full tf-card overflow-hidden">
                    <div className={`h-full ${m.color}`} style={{ width: `${Math.min(100, m.val)}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="py-10 text-center rounded-xl border border-dashed tf-subsurface space-y-2">
            <Sparkles className="w-6 h-6 text-emerald-500 mx-auto" aria-hidden="true" />
            <p className="text-xs tf-text-secondary">
              {compressionResult
                ? 'Click "Evaluate Last Compression" to score factual retention and hallucination risk.'
                : 'Execute a compression in the Workbench first, then evaluate its semantic quality here.'}
            </p>
          </div>
        )}

        {/* Strategy Ablation Grid */}
        {ablationResults.length > 0 && (
          <div className="mt-6 pt-5 space-y-3" style={{ borderTop: '1px solid var(--border-subtle)' }}>
            <h3 className="text-xs font-bold uppercase tracking-wider tf-text-secondary">
              Multi-Strategy Ranking Ablation Comparison
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {ablationResults.map((ab) => {
                const topSelected = ab.scores.filter((s) => s.selected);
                return (
                  <div key={ab.mode} className="p-4 rounded-xl tf-subsurface space-y-2.5">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold font-mono uppercase text-emerald-500">
                        {ab.mode}
                      </span>
                      <span className="text-[11px] font-mono tf-text-muted">
                        α={ab.alpha_used} • {ab.drift_detected ? 'Drift Active' : 'No Drift'}
                      </span>
                    </div>
                    <p className="text-[11px] font-mono tf-text-secondary">Strategy: {ab.ranking_strategy}</p>
                    <div className="space-y-1.5">
                      {topSelected.map((s) => (
                        <div key={s.index} className="p-2 rounded-lg tf-card text-[11px] flex items-center justify-between gap-2">
                          <span className="font-mono truncate tf-text-primary">
                            <CheckCircle2 className="w-3 h-3 inline text-emerald-500 mr-1" aria-hidden="true" />
                            #{s.index} {s.content_snippet}
                          </span>
                          <span className="font-mono font-bold text-emerald-500 shrink-0">{s.final_score.toFixed(3)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}
