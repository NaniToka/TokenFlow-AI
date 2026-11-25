import React, { useMemo, useState } from 'react';
import {
  Zap,
  Sparkles,
  FileText,
  TrendingDown,
  Copy,
  Check,
  Download,
  FileCode,
  FileSpreadsheet,
  ShieldCheck,
  DatabaseZap,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  AlertTriangle,
} from 'lucide-react';
import Card from '../common/Card';

const collator = new Intl.Collator(undefined, { numeric: true, sensitivity: 'base' });

export default function CompressionVisualizer({
  compressionResult,
  rawHistory = [],
  currentMessage = '',
  wsStage = null,
}) {
  const [activeView, setActiveView] = useState('split'); // 'split', 'diff', 'original', 'optimized'
  const [copied, setCopied] = useState(false);
  const [sortConfig, setSortConfig] = useState({ key: 'final_score', direction: 'descending' });
  const [sortStatusText, setSortStatusText] = useState('');

  const handleCopyPrompt = () => {
    if (compressionResult?.final_prompt) {
      navigator.clipboard.writeText(compressionResult.final_prompt);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleDownloadMarkdown = () => {
    if (!compressionResult) return;
    const {
      summary,
      selected_turns,
      final_prompt,
      original_tokens,
      compressed_tokens,
      tokens_saved,
      cost_saved_usd,
      compression_ratio,
    } = compressionResult;
    const turnsStr = (selected_turns || []).map((t) => `- **${t.role.toUpperCase()}**: ${t.content}`).join('\n');
    const md = `# TokenFlow AI - Context Compression Report

## Summary Metrics
- **Original Tokens**: ${original_tokens}
- **Compressed Tokens**: ${compressed_tokens}
- **Tokens Saved**: ${tokens_saved} (${compression_ratio}%)
- **Cost Saved**: $${cost_saved_usd.toFixed(6)}
- **Ranking Strategy**: ${compressionResult.metadata?.ranking_strategy || 'hybrid'}

## Background Summary
> ${summary || 'None required'}

## Retained Turns
${turnsStr}

## Final Optimized Prompt
\`\`\`text
${final_prompt}
\`\`\`
`;
    const blob = new Blob([md], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `tokenflow_report_${Date.now()}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleDownloadJson = () => {
    if (!compressionResult) return;
    const blob = new Blob([JSON.stringify(compressionResult, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `tokenflow_payload_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleDownloadCsv = () => {
    const scores = compressionResult?.metadata?.scores || [];
    if (!scores.length) return;
    const headers = ['Turn Index', 'Role', 'Snippet', 'BM25 Score', 'Semantic Score', 'Recency Score', 'Drift Penalty', 'Final Score', 'Selected'];
    const rows = scores.map((s) => [
      s.index,
      s.role,
      `"${String(s.content_snippet || '').replace(/"/g, '""')}"`,
      s.bm25_score,
      s.semantic_score,
      s.recency_score,
      s.drift_penalty,
      s.final_score,
      s.selected,
    ]);
    const csvContent = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `tokenflow_audit_${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const scoresList = useMemo(
    () => compressionResult?.metadata?.scores || [],
    [compressionResult]
  );

  const sortedScores = useMemo(() => {
    if (!scoresList.length) return [];
    const copy = [...scoresList];
    const factor = sortConfig.direction === 'ascending' ? 1 : -1;
    copy.sort((a, b) => {
      const k = sortConfig.key;
      if (k === 'role' || k === 'content_snippet') {
        return factor * collator.compare(String(a[k] || ''), String(b[k] || ''));
      }
      if (k === 'selected') {
        return factor * ((a.selected ? 1 : 0) - (b.selected ? 1 : 0));
      }
      return factor * (Number(a[k] || 0) - Number(b[k] || 0));
    });
    return copy;
  }, [scoresList, sortConfig]);

  const handleSort = (key, label) => {
    setSortConfig((prev) => {
      const nextDir = prev.key === key && prev.direction === 'ascending' ? 'descending' : 'ascending';
      setSortStatusText(`Sorted audit table by ${label}, ${nextDir}, ${scoresList.length} rows`);
      return { key, direction: nextDir };
    });
  };

  const renderSortIcon = (key) => {
    if (sortConfig.key !== key) return <ArrowUpDown className="w-3 h-3 opacity-40" aria-hidden="true" />;
    return sortConfig.direction === 'ascending' ? (
      <ArrowUp className="w-3 h-3 text-emerald-500" aria-hidden="true" />
    ) : (
      <ArrowDown className="w-3 h-3 text-emerald-500" aria-hidden="true" />
    );
  };

  const pipelineStages = [
    { id: 'init', label: '1. Sanitize & Count' },
    { id: 'ranking', label: '2. BM25 + Drift Rank' },
    { id: 'summarizing', label: '3. Cache & Summarize' },
    { id: 'complete', label: '4. Assemble Output' },
  ];

  const activeStageIdx = wsStage ? pipelineStages.findIndex((s) => s.id === wsStage.stage) : -1;

  if (!compressionResult) {
    return (
      <Card title="Prompt Compression Visualizer" subtitle="Compare uncompressed memory vs. TokenFlow optimized prompt">
        {wsStage && (
          <div className="mb-4 p-3 rounded-xl tf-subsurface space-y-2">
            <p className="text-xs font-mono font-semibold text-cyan-500">{wsStage.message}</p>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {pipelineStages.map((st, idx) => (
                <div
                  key={st.id}
                  className={`px-2.5 py-1.5 rounded-lg text-[11px] font-mono border ${
                    idx <= activeStageIdx
                      ? 'bg-emerald-500/15 border-emerald-500/40 text-emerald-500 font-bold'
                      : 'tf-card tf-text-muted'
                  }`}
                >
                  {st.label}
                </div>
              ))}
            </div>
          </div>
        )}
        <div className="py-12 p-4 flex flex-col items-center justify-center text-center space-y-3 border-2 border-dashed rounded-xl tf-subsurface">
          <div className="w-12 h-12 rounded-2xl tf-card flex items-center justify-center tf-text-muted">
            <Zap className="w-6 h-6" aria-hidden="true" />
          </div>
          <h3 className="text-sm sm:text-base font-semibold tf-text-primary">No Prompt Processed Yet</h3>
          <p className="text-xs tf-text-secondary max-w-md">
            Select a scenario above or press <kbd className="px-1.5 py-0.5 rounded tf-card font-mono text-[10px]">Ctrl+Enter</kbd> to visualize live BM25 + dense vector turn scoring and token reduction.
          </p>
        </div>
      </Card>
    );
  }

  const {
    summary = '',
    final_prompt = '',
    original_tokens = 0,
    compressed_tokens = 0,
    tokens_saved = 0,
    cost_before_usd = 0,
    cost_saved_usd = 0,
    compression_ratio = 0,
    metadata = {},
  } = compressionResult;

  const originalPromptText = rawHistory.length > 0
    ? rawHistory.map((t) => `[${t.role.toUpperCase()}]: ${t.content}`).join('\n\n') + `\n\n[USER]: ${currentMessage}`
    : `[USER]: ${currentMessage}`;

  const retainedIndices = new Set(scoresList.filter((s) => s.selected).map((s) => s.index));

  return (
    <Card
      title="Prompt Compression Visualizer & Ranking Audit"
      subtitle="Side-by-side context diff, guardrail flags, and per-turn hybrid score breakdown"
      action={
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={handleCopyPrompt}
            className="tf-btn-target flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg tf-subsurface tf-text-primary hover:opacity-85 cursor-pointer"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-500" aria-hidden="true" /> : <Copy className="w-3.5 h-3.5" aria-hidden="true" />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>

          <button
            type="button"
            onClick={handleDownloadMarkdown}
            className="tf-btn-target flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-semibold rounded-lg tf-subsurface tf-text-secondary hover:opacity-85 cursor-pointer"
          >
            <Download className="w-3.5 h-3.5 text-cyan-500" aria-hidden="true" />
            <span className="hidden sm:inline">.MD</span>
          </button>

          <button
            type="button"
            onClick={handleDownloadJson}
            className="tf-btn-target flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-semibold rounded-lg tf-subsurface tf-text-secondary hover:opacity-85 cursor-pointer"
          >
            <FileCode className="w-3.5 h-3.5 text-violet-500" aria-hidden="true" />
            <span className="hidden sm:inline">.JSON</span>
          </button>

          {scoresList.length > 0 && (
            <button
              type="button"
              onClick={handleDownloadCsv}
              className="tf-btn-target flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-semibold rounded-lg tf-subsurface tf-text-secondary hover:opacity-85 cursor-pointer"
            >
              <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-500" aria-hidden="true" />
              <span className="hidden sm:inline">.CSV</span>
            </button>
          )}

          <div className="flex items-center gap-1 p-1 rounded-xl tf-subsurface">
            {['split', 'diff', 'original', 'optimized'].map((mode) => (
              <button
                key={mode}
                type="button"
                onClick={() => setActiveView(mode)}
                className={`px-2.5 py-1 text-xs font-semibold rounded-lg capitalize transition-all cursor-pointer ${
                  activeView === mode
                    ? 'bg-emerald-500/20 text-emerald-500 border border-emerald-500/35'
                    : 'tf-text-secondary hover:opacity-85'
                }`}
              >
                {mode}
              </button>
            ))}
          </div>
        </div>
      }
    >
      {/* Live WebSocket Stage Stepper (when active) */}
      {wsStage && (
        <div className="mb-4 p-3 rounded-xl tf-subsurface grid grid-cols-2 sm:grid-cols-4 gap-2">
          {pipelineStages.map((st, idx) => (
            <div
              key={st.id}
              className={`px-2.5 py-1.5 rounded-lg text-[11px] font-mono border ${
                idx <= activeStageIdx
                  ? 'bg-emerald-500/15 border-emerald-500/40 text-emerald-500 font-bold'
                  : 'tf-card tf-text-muted'
              }`}
            >
              {st.label}
            </div>
          ))}
        </div>
      )}

      {/* Diagnostics Pills Strip */}
      <div className="flex flex-wrap items-center gap-2 mb-4">
        <span className="text-[11px] font-mono font-semibold px-2.5 py-1 rounded-lg tf-subsurface tf-text-primary">
          Strategy: <strong className="text-emerald-500">{metadata.ranking_strategy || 'hybrid'}</strong>
        </span>
        <span className="text-[11px] font-mono font-semibold px-2.5 py-1 rounded-lg tf-subsurface tf-text-primary">
          α Weight: <strong>{metadata.alpha_used ?? 0.7}</strong>
        </span>
        <span className="text-[11px] font-mono font-semibold px-2.5 py-1 rounded-lg tf-subsurface tf-text-primary">
          Latency: <strong>{metadata.latency_ms ?? 0} ms</strong>
        </span>
        {metadata.drift_detected && (
          <span className="inline-flex items-center gap-1 text-[11px] font-mono font-semibold px-2.5 py-1 rounded-lg bg-amber-500/15 text-amber-500 border border-amber-500/30">
            <AlertTriangle className="w-3.5 h-3.5" aria-hidden="true" /> Drift Penalized
          </span>
        )}
        {metadata.cache_hit && (
          <span className="inline-flex items-center gap-1 text-[11px] font-mono font-semibold px-2.5 py-1 rounded-lg bg-cyan-500/15 text-cyan-500 border border-cyan-500/30">
            <DatabaseZap className="w-3.5 h-3.5" aria-hidden="true" /> Semantic Cache HIT
          </span>
        )}
        {metadata.redaction?.enabled && (
          <span className="inline-flex items-center gap-1 text-[11px] font-mono font-semibold px-2.5 py-1 rounded-lg bg-violet-500/15 text-violet-500 border border-violet-500/30">
            <ShieldCheck className="w-3.5 h-3.5" aria-hidden="true" /> PII Guard: {metadata.redaction.redactions_count} Masked
          </span>
        )}
      </div>

      {/* Token Reduction Bar */}
      <div className="mb-6 p-4 rounded-xl tf-subsurface space-y-2 min-w-0">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between text-xs gap-1">
          <span className="font-semibold tf-text-primary flex items-center gap-2">
            <TrendingDown className="w-4 h-4 text-emerald-500 shrink-0" aria-hidden="true" />
            Token Reduction Savings: <span className="text-emerald-500 font-mono font-bold">{compression_ratio}%</span>
          </span>
          <span className="tf-text-secondary font-mono font-medium">
            {compressed_tokens} / {original_tokens} tokens ({tokens_saved} eliminated)
          </span>
        </div>
        <div className="w-full h-2.5 rounded-full overflow-hidden flex tf-card">
          <div
            className="h-full bg-gradient-to-r from-emerald-500 to-cyan-500 transition-all duration-500"
            style={{ width: `${Math.min(100, Math.max(5, (compressed_tokens / Math.max(1, original_tokens)) * 100))}%` }}
          />
        </div>
      </div>

      {/* Diff Mode */}
      {activeView === 'diff' && (
        <div className="space-y-2 mb-6 max-h-96 overflow-y-auto tf-scroller p-3 rounded-xl tf-subsurface">
          <p className="text-xs font-bold tf-text-secondary uppercase tracking-wider mb-2">
            Turn-by-Turn Retention vs. Eviction Diff ({rawHistory.length} turns)
          </p>
          {rawHistory.map((turn, idx) => {
            const kept = retainedIndices.size === 0 || retainedIndices.has(idx);
            return (
              <div
                key={idx}
                className={`p-3 rounded-lg border text-xs flex items-start gap-3 ${
                  kept
                    ? 'bg-emerald-500/10 border-emerald-500/30'
                    : 'bg-rose-500/10 border-rose-500/25 opacity-75'
                }`}
              >
                <span className={`font-mono text-[10px] font-bold px-2 py-0.5 rounded shrink-0 ${
                  kept ? 'bg-emerald-500/20 text-emerald-500' : 'bg-rose-500/20 text-rose-500'
                }`}>
                  {kept ? '+ KEPT' : '- EVICTED'} #{idx}
                </span>
                <p className={`font-mono flex-1 break-words ${kept ? 'tf-text-primary' : 'line-through tf-text-muted'}`}>
                  [{turn.role.toUpperCase()}]: {turn.content}
                </p>
              </div>
            );
          })}
        </div>
      )}

      {/* Split / Original / Optimized Panels */}
      {activeView !== 'diff' && (
        <div className={`grid gap-4 sm:gap-6 ${activeView === 'split' ? 'grid-cols-1 lg:grid-cols-2' : 'grid-cols-1'}`}>
          {(activeView === 'split' || activeView === 'original') && (
            <div className="rounded-xl tf-subsurface p-4 flex flex-col min-w-0">
              <div className="flex flex-wrap items-center justify-between pb-3 mb-3 gap-2" style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                <span className="text-xs font-bold uppercase tracking-wider text-rose-500 flex items-center gap-1.5">
                  <FileText className="w-4 h-4 shrink-0" aria-hidden="true" /> Before (Uncompressed History)
                </span>
                <div className="flex items-center gap-2 font-mono">
                  <span className="text-[11px] font-semibold px-2 py-0.5 rounded tf-card tf-text-primary">
                    {original_tokens} tok
                  </span>
                  <span className="text-[11px] font-semibold px-2 py-0.5 rounded bg-rose-500/10 text-rose-500 border border-rose-500/25">
                    ${cost_before_usd.toFixed(6)}
                  </span>
                </div>
              </div>
              <div className="overflow-auto tf-scroller max-h-96">
                <pre className="text-xs tf-text-secondary font-mono whitespace-pre-wrap leading-relaxed pr-2">
                  {originalPromptText}
                </pre>
              </div>
            </div>
          )}

          {(activeView === 'split' || activeView === 'optimized') && (
            <div className="rounded-xl tf-subsurface border border-emerald-500/40 p-4 flex flex-col min-w-0">
              <div className="flex flex-wrap items-center justify-between pb-3 mb-3 gap-2" style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                <span className="text-xs font-bold uppercase tracking-wider text-emerald-500 flex items-center gap-1.5">
                  <Sparkles className="w-4 h-4 shrink-0" aria-hidden="true" /> After (TokenFlow Optimized)
                </span>
                <div className="flex items-center gap-2 font-mono">
                  <span className="text-[11px] font-semibold px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-500 border border-emerald-500/30">
                    {compressed_tokens} tok
                  </span>
                  <span className="text-[11px] font-semibold px-2 py-0.5 rounded bg-cyan-500/15 text-cyan-500 border border-cyan-500/30">
                    Saved ${cost_saved_usd.toFixed(6)}
                  </span>
                </div>
              </div>

              {summary && (
                <div className="mb-4 p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-xs">
                  <div className="flex items-center gap-1.5 text-emerald-500 font-bold mb-1">
                    <Zap className="w-3.5 h-3.5 shrink-0" aria-hidden="true" /> Synthesized Background Memory
                  </div>
                  <p className="tf-text-primary leading-relaxed">{summary}</p>
                </div>
              )}

              <div className="overflow-auto tf-scroller max-h-96">
                <pre className="text-xs tf-text-primary font-mono whitespace-pre-wrap leading-relaxed pr-2">
                  {final_prompt}
                </pre>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Sortable Responsive Audit Table (modern-web-guidance compliant) */}
      {sortedScores.length > 0 && (
        <div className="mt-6 pt-5" style={{ borderTop: '1px solid var(--border-subtle)' }}>
          <div className="flex items-center justify-between mb-3">
            <h3 id="audit-table-heading" className="text-xs font-bold uppercase tracking-wider tf-text-secondary">
              Per-Turn Hybrid Ranking Audit &amp; Score Waterfall ({sortedScores.length} Turns)
            </h3>
            <span className="text-[11px] font-mono tf-text-muted">Click column headers to sort</span>
          </div>

          <div role="status" className="visually-hidden">{sortStatusText}</div>

          <div
            tabIndex={0}
            role="region"
            aria-labelledby="audit-table-caption"
            className="tf-table-wrapper tf-scroller"
          >
            <table className="tf-audit-table">
              <caption id="audit-table-caption" className="visually-hidden">
                Per-turn BM25, semantic similarity, recency decay, drift penalty, and selection audit
              </caption>
              <thead>
                <tr>
                  <th
                    scope="col"
                    aria-sort={sortConfig.key === 'index' ? sortConfig.direction : undefined}
                  >
                    <button type="button" onClick={() => handleSort('index', 'Turn Index')}>
                      <span>#</span> {renderSortIcon('index')}
                    </button>
                  </th>
                  <th
                    scope="col"
                    aria-sort={sortConfig.key === 'role' ? sortConfig.direction : undefined}
                  >
                    <button type="button" onClick={() => handleSort('role', 'Role')}>
                      <span>Role</span> {renderSortIcon('role')}
                    </button>
                  </th>
                  <th scope="col">Turn Snippet</th>
                  <th
                    scope="col"
                    aria-sort={sortConfig.key === 'bm25_score' ? sortConfig.direction : undefined}
                  >
                    <button type="button" onClick={() => handleSort('bm25_score', 'BM25')}>
                      <span>BM25</span> {renderSortIcon('bm25_score')}
                    </button>
                  </th>
                  <th
                    scope="col"
                    aria-sort={sortConfig.key === 'semantic_score' ? sortConfig.direction : undefined}
                  >
                    <button type="button" onClick={() => handleSort('semantic_score', 'Semantic')}>
                      <span>Semantic</span> {renderSortIcon('semantic_score')}
                    </button>
                  </th>
                  <th
                    scope="col"
                    aria-sort={sortConfig.key === 'recency_score' ? sortConfig.direction : undefined}
                  >
                    <button type="button" onClick={() => handleSort('recency_score', 'Recency')}>
                      <span>Recency</span> {renderSortIcon('recency_score')}
                    </button>
                  </th>
                  <th
                    scope="col"
                    aria-sort={sortConfig.key === 'drift_penalty' ? sortConfig.direction : undefined}
                  >
                    <button type="button" onClick={() => handleSort('drift_penalty', 'Drift')}>
                      <span>Drift</span> {renderSortIcon('drift_penalty')}
                    </button>
                  </th>
                  <th
                    scope="col"
                    aria-sort={sortConfig.key === 'final_score' ? sortConfig.direction : undefined}
                  >
                    <button type="button" onClick={() => handleSort('final_score', 'Final Score')}>
                      <span>Score</span> {renderSortIcon('final_score')}
                    </button>
                  </th>
                  <th
                    scope="col"
                    aria-sort={sortConfig.key === 'selected' ? sortConfig.direction : undefined}
                  >
                    <button type="button" onClick={() => handleSort('selected', 'Decision')}>
                      <span>Status</span> {renderSortIcon('selected')}
                    </button>
                  </th>
                </tr>
              </thead>
              <tbody>
                {sortedScores.map((item) => (
                  <tr key={item.index}>
                    <th scope="row" className="font-mono tf-text-muted">#{item.index}</th>
                    <td data-label="Role">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                        item.role === 'user'
                          ? 'bg-cyan-500/15 text-cyan-500'
                          : 'bg-violet-500/15 text-violet-500'
                      }`}>
                        {item.role}
                      </span>
                    </td>
                    <td data-label="Snippet" className="font-mono max-w-[240px] truncate tf-text-primary">
                      {item.content_snippet}
                    </td>
                    <td data-label="BM25" className="font-mono">{Number(item.bm25_score || 0).toFixed(3)}</td>
                    <td data-label="Semantic" className="font-mono">{Number(item.semantic_score || 0).toFixed(3)}</td>
                    <td data-label="Recency" className="font-mono">{Number(item.recency_score || 0).toFixed(3)}</td>
                    <td data-label="Drift" className="font-mono text-amber-500">
                      {item.drift_penalty > 0 ? `-${Number(item.drift_penalty).toFixed(3)}` : '0.000'}
                    </td>
                    <td data-label="Final Score" className="font-mono font-bold">
                      <div className="flex items-center gap-2">
                        <span>{Number(item.final_score || 0).toFixed(3)}</span>
                        <div className="w-16 h-1.5 rounded-full tf-subsurface overflow-hidden hidden sm:block">
                          <div
                            className="h-full bg-emerald-500"
                            style={{ width: `${Math.min(100, (item.final_score || 0) * 100)}%` }}
                          />
                        </div>
                      </div>
                    </td>
                    <td data-label="Decision">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                        item.selected
                          ? 'bg-emerald-500/15 text-emerald-500 border border-emerald-500/30'
                          : 'tf-subsurface tf-text-muted'
                      }`}>
                        {item.selected ? 'Retained' : 'Evicted'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </Card>
  );
}
