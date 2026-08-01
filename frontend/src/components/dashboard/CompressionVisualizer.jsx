import React, { useState } from 'react';
import { Zap, Sparkles, FileText, TrendingDown, Copy, Check } from 'lucide-react';
import Card from '../common/Card';

export default function CompressionVisualizer({ compressionResult, rawHistory = [], currentMessage = '' }) {
  const [activeView, setActiveView] = useState('split'); // 'split', 'original', 'optimized'
  const [copied, setCopied] = useState(false);

  const handleCopyPrompt = () => {
    if (compressionResult?.final_prompt) {
      navigator.clipboard.writeText(compressionResult.final_prompt);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (!compressionResult) {
    return (
      <Card title="Prompt Compression Visualizer" subtitle="Compare uncompressed memory vs. TokenFlow optimized prompt">
        <div className="py-16 flex flex-col items-center justify-center text-center space-y-3 border-2 border-dashed border-zinc-800 rounded-xl bg-zinc-950/40">
          <div className="w-12 h-12 rounded-2xl bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-500">
            <Zap className="w-6 h-6" />
          </div>
          <h4 className="text-base font-semibold text-zinc-300">No Prompt Processed Yet</h4>
          <p className="text-xs text-zinc-500 max-w-sm">
            Load a 30-turn demo scenario or type a custom prompt to view live semantic ranking and before/after token reduction.
          </p>
        </div>
      </Card>
    );
  }

  const {
    summary = '',
    selected_turns = [],
    final_prompt = '',
    original_tokens = 0,
    compressed_tokens = 0,
    tokens_saved = 0,
    cost_before_usd = 0,
    cost_saved_usd = 0,
    compression_ratio = 0
  } = compressionResult;

  // Format full original prompt text
  const originalPromptText = rawHistory.length > 0
    ? rawHistory.map((t) => `[${t.role.toUpperCase()}]: ${t.content}`).join('\n\n') + `\n\n[USER]: ${currentMessage}`
    : `[USER]: ${currentMessage}`;

  return (
    <Card
      title="Prompt Compression Visualizer"
      subtitle="Side-by-side semantic memory comparison & turn ranking metadata"
      action={
        <div className="flex items-center gap-2">
          <button
            onClick={handleCopyPrompt}
            className="flex items-center gap-1.5 px-3 py-1 text-xs font-semibold rounded-lg bg-zinc-900 hover:bg-zinc-800 text-zinc-200 border border-zinc-700 transition-all active:scale-95"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5 text-zinc-400" />}
            <span>{copied ? 'Copied!' : 'Copy Final Prompt'}</span>
          </button>

          <div className="flex items-center gap-1 bg-zinc-950 p-1 rounded-xl border border-white/5">
            <button
              onClick={() => setActiveView('split')}
              className={`px-3 py-1 text-xs font-semibold rounded-lg transition-all ${
                activeView === 'split' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'text-zinc-400 hover:text-zinc-200'
              }`}
            >
              Split View
            </button>
            <button
              onClick={() => setActiveView('original')}
              className={`px-3 py-1 text-xs font-semibold rounded-lg transition-all ${
                activeView === 'original' ? 'bg-zinc-800 text-zinc-200' : 'text-zinc-400 hover:text-zinc-200'
              }`}
            >
              Original
            </button>
            <button
              onClick={() => setActiveView('optimized')}
              className={`px-3 py-1 text-xs font-semibold rounded-lg transition-all ${
                activeView === 'optimized' ? 'bg-emerald-500/20 text-emerald-400' : 'text-zinc-400 hover:text-zinc-200'
              }`}
            >
              Optimized
            </button>
          </div>
        </div>
      }
    >
      {/* Compression Progress Bar */}
      <div className="mb-6 p-4 rounded-xl bg-zinc-950/70 border border-white/5 space-y-2">
        <div className="flex items-center justify-between text-xs">
          <span className="font-semibold text-zinc-300 flex items-center gap-2">
            <TrendingDown className="w-4 h-4 text-emerald-400" />
            Token Reduction Savings: <span className="text-emerald-400 font-bold">{compression_ratio}%</span>
          </span>
          <span className="text-zinc-400 font-medium">
            {compressed_tokens} / {original_tokens} tokens ({tokens_saved} saved)
          </span>
        </div>
        <div className="w-full h-2.5 bg-zinc-900 rounded-full overflow-hidden flex border border-white/5">
          <div
            className="h-full bg-gradient-to-r from-emerald-500 to-cyan-500 transition-all duration-500"
            style={{ width: `${Math.min(100, Math.max(5, (compressed_tokens / original_tokens) * 100))}%` }}
          />
          <div
            className="h-full bg-zinc-800/80 transition-all duration-500"
            style={{ width: `${100 - Math.min(100, Math.max(5, (compressed_tokens / original_tokens) * 100))}%` }}
          />
        </div>
      </div>

      {/* Split Comparison Panels */}
      <div className={`grid gap-6 ${activeView === 'split' ? 'grid-cols-1 lg:grid-cols-2' : 'grid-cols-1'}`}>
        {/* Left Panel: Original Uncompressed */}
        {(activeView === 'split' || activeView === 'original') && (
          <div className="rounded-xl bg-zinc-950/80 border border-zinc-800 p-4 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between border-b border-zinc-800 pb-3 mb-3">
                <span className="text-xs font-bold uppercase tracking-wider text-rose-400 flex items-center gap-1.5">
                  <FileText className="w-4 h-4" /> Before (Full Raw Context)
                </span>
                <div className="flex items-center gap-2">
                  <span className="text-[11px] font-semibold px-2 py-0.5 rounded bg-zinc-900 border border-zinc-800 text-zinc-300">
                    {original_tokens} tokens
                  </span>
                  <span className="text-[11px] font-semibold px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20">
                    ${cost_before_usd.toFixed(6)}
                  </span>
                </div>
              </div>
              <pre className="text-xs text-zinc-400 font-mono whitespace-pre-wrap leading-relaxed max-h-96 overflow-y-auto pr-2 select-all">
                {originalPromptText}
              </pre>
            </div>
          </div>
        )}

        {/* Right Panel: Optimized Compressed */}
        {(activeView === 'split' || activeView === 'optimized') && (
          <div className="rounded-xl bg-zinc-950/80 border border-emerald-500/30 p-4 flex flex-col justify-between glow-emerald">
            <div>
              <div className="flex items-center justify-between border-b border-emerald-500/20 pb-3 mb-3">
                <span className="text-xs font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-1.5">
                  <Sparkles className="w-4 h-4 text-emerald-400" /> After (TokenFlow Optimized)
                </span>
                <div className="flex items-center gap-2">
                  <span className="text-[11px] font-semibold px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                    {compressed_tokens} tokens
                  </span>
                  <span className="text-[11px] font-semibold px-2 py-0.5 rounded bg-cyan-500/15 text-cyan-300 border border-cyan-500/30">
                    Saved ${cost_saved_usd.toFixed(6)}
                  </span>
                </div>
              </div>

              {/* Highlighted Background Summary Block */}
              {summary && (
                <div className="mb-4 p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-xs">
                  <div className="flex items-center gap-1.5 text-emerald-400 font-semibold mb-1">
                    <Zap className="w-3.5 h-3.5" /> Background Context Summary (Gemini 1.5 Flash)
                  </div>
                  <p className="text-zinc-200 leading-relaxed font-sans">{summary}</p>
                </div>
              )}

              <pre className="text-xs text-zinc-300 font-mono whitespace-pre-wrap leading-relaxed max-h-96 overflow-y-auto pr-2 select-all">
                {final_prompt}
              </pre>
            </div>
          </div>
        )}
      </div>

      {/* Selected Turns List */}
      {selected_turns.length > 0 && (
        <div className="mt-6 border-t border-white/5 pt-4">
          <h4 className="text-xs font-bold uppercase tracking-wider text-zinc-400 mb-3">
            Top-K Chronological Memory Turns Retained ({selected_turns.length})
          </h4>
          <div className="space-y-2">
            {selected_turns.map((turn, i) => (
              <div key={i} className="p-2.5 rounded-lg bg-zinc-950/60 border border-zinc-800 text-xs flex items-start gap-3">
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                  turn.role === 'user' ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30' : 'bg-violet-500/20 text-violet-400 border border-violet-500/30'
                }`}>
                  {turn.role}
                </span>
                <p className="text-zinc-300 flex-1 font-mono">{turn.content}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </Card>
  );
}
