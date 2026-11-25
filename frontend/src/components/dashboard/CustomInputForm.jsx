import React, { useState } from 'react';
import { Sparkles, AlertCircle, FileCode, Shield } from 'lucide-react';
import Card from '../common/Card';

const SAMPLE_JSON = JSON.stringify([
  { role: 'user', content: 'I am designing a microservices application using Python FastAPI with PostgreSQL.' },
  { role: 'model', content: 'What connection pooler and caching layers are you deploying?' },
  { role: 'user', content: 'PgBouncer + Redis, and contact dev@acme.org with key sk-abcdef1234567890abcdef1234567890.' },
  { role: 'model', content: 'Great! Ensure TLS 1.3 and key rotation policies are active.' },
  { role: 'user', content: 'Wait, what did you have for lunch today?' },
  { role: 'model', content: 'As an AI assistant, I do not eat lunch.' },
], null, 2);

export default function CustomInputForm({
  customQuery,
  onQueryChange,
  rawHistoryJson,
  onRawHistoryChange,
  sanitizePii,
  onSanitizePiiChange,
  onExecuteCompression,
  isCompressing,
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
    } catch {
      try {
        parsed = JSON.parse(`[${trimmed}]`);
      } catch {
        return [{ role: 'user', content: trimmed }];
      }
    }

    if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
      parsed = [parsed];
    }

    if (!Array.isArray(parsed)) {
      return [{ role: 'user', content: trimmed }];
    }

    const normalized = [];
    for (let i = 0; i < parsed.length; i++) {
      const item = parsed[i];
      if (typeof item === 'string') {
        normalized.push({ role: 'user', content: item });
        continue;
      }
      if (item && typeof item === 'object') {
        const rawRole = String(item.role || item.type || item.author || 'user').toLowerCase();
        const validRole = rawRole === 'assistant' || rawRole === 'system' || rawRole === 'model' ? 'model' : 'user';
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
    <Card title="Custom JSON Context & Raw Prompt Optimizer" subtitle="Paste raw multi-turn JSON logs and test PII redaction + hybrid ranking">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="custom-query-input" className="block text-xs font-bold tf-text-secondary mb-1.5 uppercase tracking-wider">
            Current User Query <span className="text-rose-500">*</span>
          </label>
          <input
            id="custom-query-input"
            type="text"
            value={customQuery}
            onChange={(e) => {
              onQueryChange(e.target.value);
              if (jsonError) setJsonError(null);
            }}
            placeholder="Type current user query..."
            className="tf-input w-full px-4 py-2.5 text-sm"
          />
        </div>

        <div>
          <div className="flex items-center justify-between mb-1.5">
            <label htmlFor="custom-history-json" className="block text-xs font-bold tf-text-secondary uppercase tracking-wider">
              Conversation History JSON Array
            </label>
            <button
              type="button"
              onClick={handlePasteExample}
              className="text-xs font-semibold text-emerald-500 hover:underline flex items-center gap-1 cursor-pointer"
            >
              <FileCode className="w-3.5 h-3.5" aria-hidden="true" /> Load Sample with Drift &amp; PII
            </button>
          </div>

          <textarea
            id="custom-history-json"
            value={rawHistoryJson}
            onChange={(e) => {
              onRawHistoryChange(e.target.value);
              if (jsonError) setJsonError(null);
            }}
            rows={6}
            placeholder='[{"role": "user", "content": "Hello"}, {"role": "model", "content": "Hi there"}]'
            className="tf-input w-full px-4 py-2.5 text-xs font-mono resize-y"
          />
        </div>

        {jsonError && (
          <div role="alert" className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-500 text-xs flex items-start gap-2.5">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" aria-hidden="true" />
            <div>
              <p className="font-bold">Validation Error</p>
              <p className="font-mono text-[11px] mt-0.5">{jsonError}</p>
            </div>
          </div>
        )}

        <div className="flex flex-wrap items-center justify-between gap-3 pt-3" style={{ borderTop: '1px solid var(--border-subtle)' }}>
          <label className="flex items-center gap-2 text-xs font-medium tf-text-primary cursor-pointer">
            <input
              type="checkbox"
              checked={sanitizePii}
              onChange={(e) => onSanitizePiiChange(e.target.checked)}
              className="w-4 h-4 rounded"
            />
            <Shield className="w-4 h-4 text-amber-500" aria-hidden="true" />
            <span>Enable PII &amp; API Key Redaction</span>
          </label>

          <button
            type="submit"
            disabled={isCompressing}
            className="tf-btn-target flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-400 hover:to-cyan-400 text-zinc-950 font-bold text-xs shadow-lg shadow-emerald-500/20 transition-all active:scale-95 disabled:opacity-50 cursor-pointer"
          >
            <Sparkles className={`w-4 h-4 ${isCompressing ? 'animate-spin' : ''}`} aria-hidden="true" />
            <span>{isCompressing ? 'Compressing...' : 'Execute Compression'}</span>
          </button>
        </div>
      </form>
    </Card>
  );
}
