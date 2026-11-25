import React, { useState } from 'react';
import { Plus, Trash2, Send, Sparkles, AlertTriangle, Bot, User } from 'lucide-react';
import Card from '../common/Card';

const NOISE_TURNS = [
  { role: 'user', content: 'By the way, what is the weather in Tokyo right now and did you watch the football match?' },
  { role: 'model', content: 'Tokyo is around 19°C and partly cloudy. I do not track live sports scores!' },
];

export default function ConversationPlayground({
  history,
  onHistoryChange,
  query,
  onQueryChange,
  onRunCompression,
  isCompressing,
}) {
  const [newRole, setNewRole] = useState('user');
  const [newContent, setNewContent] = useState('');

  const handleAddTurn = (e) => {
    e.preventDefault();
    if (!newContent.trim()) return;
    onHistoryChange([...history, { role: newRole, content: newContent.trim() }]);
    setNewContent('');
    setNewRole((prev) => (prev === 'user' ? 'model' : 'user'));
  };

  const handleInjectDrift = () => {
    onHistoryChange([...history, ...NOISE_TURNS]);
  };

  const handleDeleteTurn = (idx) => {
    onHistoryChange(history.filter((_, i) => i !== idx));
  };

  return (
    <Card
      title="Interactive Multi-Turn Conversation Playground"
      subtitle="Build, edit, or inject conversational drift into live dialogue histories before compression"
      action={
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={handleInjectDrift}
            className="tf-btn-target flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-amber-500/15 text-amber-500 border border-amber-500/30 text-xs font-semibold hover:opacity-90 cursor-pointer"
          >
            <AlertTriangle className="w-3.5 h-3.5" aria-hidden="true" />
            <span>Inject Drift Noise</span>
          </button>

          <button
            type="button"
            onClick={() => onRunCompression(history, query)}
            disabled={isCompressing || !query.trim()}
            className="tf-btn-target flex items-center gap-1.5 px-4 py-1.5 rounded-xl bg-gradient-to-r from-emerald-500 to-cyan-500 text-zinc-950 font-bold text-xs shadow-md transition-all active:scale-95 disabled:opacity-50 cursor-pointer"
          >
            <Sparkles className={`w-3.5 h-3.5 ${isCompressing ? 'animate-spin' : ''}`} aria-hidden="true" />
            <span>{isCompressing ? 'Optimizing...' : 'Compress Dialogue'}</span>
          </button>
        </div>
      }
    >
      <div className="space-y-4">
        {/* Timeline of Turns */}
        <div className="space-y-2.5 max-h-96 overflow-y-auto tf-scroller pr-1">
          {history.map((turn, idx) => (
            <div
              key={idx}
              className="p-3 rounded-xl tf-subsurface flex items-start justify-between gap-3 group"
            >
              <div className="flex items-start gap-2.5 min-w-0 flex-1">
                <div className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 mt-0.5 ${
                  turn.role === 'user' ? 'bg-cyan-500/15 text-cyan-500' : 'bg-violet-500/15 text-violet-500'
                }`}>
                  {turn.role === 'user' ? <User className="w-3.5 h-3.5" aria-hidden="true" /> : <Bot className="w-3.5 h-3.5" aria-hidden="true" />}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="text-[10px] font-mono font-bold uppercase tf-text-muted">
                      Turn #{idx} • {turn.role}
                    </span>
                  </div>
                  <p className="text-xs tf-text-primary break-words font-mono leading-relaxed">
                    {turn.content}
                  </p>
                </div>
              </div>

              <button
                type="button"
                onClick={() => handleDeleteTurn(idx)}
                aria-label={`Remove turn ${idx}`}
                className="tf-btn-target p-1.5 rounded-lg text-rose-500 hover:bg-rose-500/15 shrink-0 cursor-pointer"
              >
                <Trash2 className="w-3.5 h-3.5" aria-hidden="true" />
              </button>
            </div>
          ))}
        </div>

        {/* Append New Turn Form */}
        <form onSubmit={handleAddTurn} className="p-3.5 rounded-xl tf-subsurface space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <label htmlFor="playground-role" className="text-xs font-semibold tf-text-secondary">
              Append Role:
            </label>
            <select
              id="playground-role"
              value={newRole}
              onChange={(e) => setNewRole(e.target.value)}
              className="tf-input px-2.5 py-1 text-xs font-mono"
            >
              <option value="user">user</option>
              <option value="model">model</option>
            </select>
          </div>

          <div className="flex flex-col sm:flex-row gap-2">
            <input
              type="text"
              value={newContent}
              onChange={(e) => setNewContent(e.target.value)}
              placeholder="Add a technical turn or tangential comment..."
              aria-label="New turn content"
              className="tf-input flex-1 px-3 py-2 text-xs"
            />
            <button
              type="submit"
              className="tf-btn-target flex items-center justify-center gap-1.5 px-4 py-2 rounded-xl tf-card font-semibold text-xs tf-text-primary hover:border-emerald-500/40 cursor-pointer"
            >
              <Plus className="w-3.5 h-3.5 text-emerald-500" aria-hidden="true" />
              <span>Append Turn</span>
            </button>
          </div>
        </form>

        {/* Final Current User Query */}
        <div className="p-3.5 rounded-xl bg-emerald-500/5 border border-emerald-500/25 space-y-2">
          <label htmlFor="playground-current-query" className="block text-xs font-bold text-emerald-500 uppercase tracking-wider">
            Target Current Message
          </label>
          <div className="flex flex-col sm:flex-row gap-2">
            <input
              id="playground-current-query"
              type="text"
              value={query}
              onChange={(e) => onQueryChange(e.target.value)}
              className="tf-input flex-1 px-3 py-2 text-xs font-medium"
            />
            <button
              type="button"
              onClick={() => onRunCompression(history, query)}
              disabled={isCompressing || !query.trim()}
              className="tf-btn-target flex items-center justify-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-500 text-zinc-950 font-bold text-xs cursor-pointer disabled:opacity-50"
            >
              <Send className="w-3.5 h-3.5" aria-hidden="true" />
              <span>Test Compression</span>
            </button>
          </div>
        </div>
      </div>
    </Card>
  );
}
