import React, { useEffect, useRef, useState } from 'react';
import { Search, X, ArrowRight, Terminal, Zap, Cpu, BarChart3, BookOpen, ShieldCheck, Settings, FlaskConical, SunMoon } from 'lucide-react';

/**
 * Native <dialog closedby="any"> Command Palette (Cmd+K / Ctrl+K)
 * Follows modern-web-guidance: uses showModal(), closedby="any" + pointer fallback,
 * no redundant role="dialog" or aria-modal, and h1 heading inside modal scope.
 */
export default function CommandPalette({
  isOpen,
  onClose,
  onNavigate,
  onRunCompression,
  onToggleTheme,
  presets = [],
  onSelectPreset,
}) {
  const dialogRef = useRef(null);
  const [query, setQuery] = useState('');

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    if (isOpen && !dialog.open) {
      setQuery('');
      dialog.showModal();
    } else if (!isOpen && dialog.open) {
      dialog.close();
    }
  }, [isOpen]);

  // Light-dismiss fallback for browsers without native closedBy support
  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    const handleClose = () => onClose();
    dialog.addEventListener('close', handleClose);

    if (!('closedBy' in HTMLDialogElement.prototype)) {
      let pressedOutside = false;
      const outside = (e) => {
        const r = dialog.getBoundingClientRect();
        return e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom;
      };
      const onDown = (e) => { pressedOutside = outside(e); };
      const onUp = (e) => { if (pressedOutside && outside(e)) dialog.close(); };
      dialog.addEventListener('pointerdown', onDown);
      dialog.addEventListener('pointerup', onUp);
      return () => {
        dialog.removeEventListener('close', handleClose);
        dialog.removeEventListener('pointerdown', onDown);
        dialog.removeEventListener('pointerup', onUp);
      };
    }

    return () => dialog.removeEventListener('close', handleClose);
  }, [onClose]);

  const actions = [
    { id: 'act-run', group: 'Execution', label: 'Execute Context Compression', hint: 'Ctrl+Enter', icon: Zap, run: onRunCompression },
    { id: 'act-theme', group: 'Appearance', label: 'Cycle Color Theme (Light / Dark)', hint: 'Theme', icon: SunMoon, run: onToggleTheme },
    { id: 'nav-opt', group: 'Navigation', label: 'Go to Context Workbench', hint: 'Workbench', icon: Cpu, run: () => onNavigate('optimizer') },
    { id: 'nav-play', group: 'Navigation', label: 'Go to Interactive Chat Playground', hint: 'Playground', icon: Terminal, run: () => onNavigate('playground') },
    { id: 'nav-rag', group: 'Navigation', label: 'Go to RAG Chunker & Retriever Lab', hint: 'RAG Lab', icon: BookOpen, run: () => onNavigate('rag') },
    { id: 'nav-eval', group: 'Navigation', label: 'Go to LLM-as-Judge Quality Studio', hint: 'Evaluator', icon: FlaskConical, run: () => onNavigate('evaluator') },
    { id: 'nav-ana', group: 'Navigation', label: 'Go to Telemetry & P95 Analytics', hint: 'Telemetry', icon: BarChart3, run: () => onNavigate('analytics') },
    { id: 'nav-sec', group: 'Navigation', label: 'Go to PII Guard & Settings', hint: 'Settings', icon: ShieldCheck, run: () => onNavigate('settings') },
    ...presets.slice(0, 8).map((p) => ({
      id: `preset-${p.id}`,
      group: 'Scenarios',
      label: `Load Scenario: ${p.title}`,
      hint: p.domain,
      icon: Settings,
      run: () => {
        onSelectPreset(p.id);
        onNavigate('optimizer');
      },
    })),
  ];

  const q = query.trim().toLowerCase();
  const filtered = q
    ? actions.filter((a) => a.label.toLowerCase().includes(q) || a.group.toLowerCase().includes(q) || a.hint.toLowerCase().includes(q))
    : actions;

  return (
    <dialog
      ref={dialogRef}
      closedby="any"
      aria-labelledby="cmd-palette-title"
      className="tf-dialog"
    >
      <div className="p-4 sm:p-5 space-y-3">
        <div className="flex items-center justify-between gap-3 pb-3" style={{ borderBottom: '1px solid var(--border-subtle)' }}>
          <div className="flex items-center gap-2.5 flex-1 min-w-0">
            <Search className="w-4 h-4 shrink-0" style={{ color: 'var(--accent-primary)' }} aria-hidden="true" />
            <h1 id="cmd-palette-title" className="visually-hidden">Command Palette</h1>
            <input
              type="search"
              autofocus
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Type a command, workspace view, or scenario..."
              aria-label="Search commands and scenarios"
              className="w-full bg-transparent text-sm tf-text-primary outline-none placeholder:opacity-60"
            />
          </div>
          <button
            type="button"
            onClick={() => dialogRef.current?.close()}
            aria-label="Close command palette"
            className="tf-btn-target p-1.5 rounded-lg tf-subsurface tf-text-secondary hover:opacity-80 cursor-pointer"
          >
            <X className="w-4 h-4" aria-hidden="true" />
          </button>
        </div>

        <div className="max-h-80 overflow-y-auto tf-scroller space-y-1 pr-1">
          {filtered.length === 0 ? (
            <p className="text-xs tf-text-muted py-6 text-center">No commands matching &ldquo;{query}&rdquo;</p>
          ) : (
            filtered.map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => {
                    item.run();
                    dialogRef.current?.close();
                  }}
                  className="w-full flex items-center justify-between gap-3 px-3 py-2.5 rounded-xl text-left text-xs transition-colors hover:bg-emerald-500/10 cursor-pointer"
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    <Icon className="w-4 h-4 shrink-0" style={{ color: 'var(--accent-primary)' }} aria-hidden="true" />
                    <span className="font-medium tf-text-primary truncate">{item.label}</span>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded tf-subsurface tf-text-muted">
                      {item.hint}
                    </span>
                    <ArrowRight className="w-3.5 h-3.5 tf-text-muted" aria-hidden="true" />
                  </div>
                </button>
              );
            })
          )}
        </div>
      </div>
    </dialog>
  );
}
