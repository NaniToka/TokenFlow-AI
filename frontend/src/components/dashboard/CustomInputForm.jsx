import React, { useState } from 'react';
import { Sparkles, AlertCircle, FileCode } from 'lucide-react';
import Card from '../common/Card';

const SAMPLE_JSON = JSON.stringify([
  { "role": "user", "content": "I am designing a microservices application using Python FastAPI." },
  { "role": "model", "content": "That sounds great! What database and caching layers are you planning to use?" },
  { "role": "user", "content": "We are using PostgreSQL with SQLAlchemy 2.0 and Redis for caching." }
], null, 2);

export default function CustomInputForm({
  customQuery,
  onQueryChange,
  rawHistoryJson,
  onRawHistoryChange,
  onExecuteCompression,
  isCompressing
}) {
  const [jsonError, setJsonError] = useState(null);

  const handlePasteExample = () => {
    onRawHistoryChange(SAMPLE_JSON);
    setJsonError(null);
  };

  const parseAndNormalizeInput = (inputString) => {
    const trimmed = inputString.trim();
    if (!trimmed) return [];

    let parsed;
    try {
      parsed = JSON.parse(trimmed);
    } catch (err) {
      // Try wrapping in brackets if user provided comma-separated objects without outer [ ]
      try {
        parsed = JSON.parse(`[${trimmed}]`);
      } catch (err2) {
        // Fallback: If it's plain text, treat as a single user turn
        return [{ role: 'user', content: trimmed }];
      }
    }

    // Auto-wrap single object into array
    if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
      parsed = [parsed];
    }

    if (!Array.isArray(parsed)) {
      return [{ role: 'user', content: trimmed }];
    }

    // Normalize each turn item safely
    const normalized = [];
    for (let i = 0; i < parsed.length; i++) {
      let item = parsed[i];
      if (typeof item === 'string') {
        normalized.push({ role: 'user', content: item });
        continue;
      }
      if (item && typeof item === 'object') {
        const rawRole = (item.role || item.type || item.author || 'user').toLowerCase();
        const validRole = (rawRole === 'assistant' || rawRole === 'system' || rawRole === 'model')
          ? 'model'
          : 'user';
        const content = item.content || item.text || item.message || item.prompt || JSON.stringify(item);
        if (content && String(content).trim()) {
          normalized.push({ role: validRole, content: String(content).trim() });
        }
      }
    }
    return normalized;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setJsonError(null);

    if (!customQuery || !customQuery.trim()) {
      setJsonError('Current User Message cannot be empty.');
      return;
    }

    const parsedHistory = parseAndNormalizeInput(rawHistoryJson || '');
    onExecuteCompression(parsedHistory, customQuery.trim());
  };

  return (
    <Card title="Custom Input Prompt & Raw JSON History" subtitle="Paste custom conversation history turns and test compression">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-semibold text-zinc-400 mb-1.5 uppercase tracking-wider">
            Current User Message <span className="text-rose-400">*</span>
          </label>
          <input
            type="text"
            value={customQuery}
            onChange={(e) => {
              onQueryChange(e.target.value);
              if (jsonError) setJsonError(null);
            }}
            placeholder="Type current user query..."
            className="glass-input w-full px-4 py-2.5 text-sm"
          />
        </div>

        <div>
          <div className="flex items-center justify-between mb-1.5">
            <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider">
              Custom History JSON Array or Single Object (Optional)
            </label>
            <button
              type="button"
              onClick={handlePasteExample}
              className="text-xs font-semibold text-emerald-400 hover:text-emerald-300 flex items-center gap-1 transition-all"
            >
              <FileCode className="w-3.5 h-3.5" /> Paste Example JSON Array
            </button>
          </div>

          <textarea
            value={rawHistoryJson}
            onChange={(e) => {
              onRawHistoryChange(e.target.value);
              if (jsonError) setJsonError(null);
            }}
            rows={6}
            placeholder='{"role": "user", "content": "Hello"}  or  [{"role": "user", "content": "hello"}]'
            className="glass-input w-full px-4 py-2.5 text-xs font-mono"
          />
        </div>

        {jsonError && (
          <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-start gap-2.5">
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-rose-300">Validation Error</p>
              <p className="text-zinc-300 font-mono text-[11px] mt-0.5">{jsonError}</p>
            </div>
          </div>
        )}

        <div className="flex items-center justify-end gap-3 pt-2 border-t border-white/5">
          <button
            type="submit"
            disabled={isCompressing}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-400 hover:to-cyan-400 text-zinc-950 font-bold text-xs shadow-lg shadow-emerald-500/20 transition-all active:scale-95 disabled:opacity-50"
          >
            <Sparkles className={`w-4 h-4 ${isCompressing ? 'animate-spin' : ''}`} />
            <span>{isCompressing ? 'Compressing...' : 'Execute Compression'}</span>
          </button>
        </div>
      </form>
    </Card>
  );
}
