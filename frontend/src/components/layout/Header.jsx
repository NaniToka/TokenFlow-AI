import React, { useState, useEffect } from 'react';
import { RotateCcw, Sparkles, Clock, Menu, Search, Keyboard, Sun, Moon, Radio } from 'lucide-react';

const TRANSPORTS = [
  { id: 'rest', label: 'REST' },
  { id: 'ws', label: 'WS' },
  { id: 'sse', label: 'SSE' },
];

export default function Header({
  onResetStats,
  isResetting = false,
  onToggleMobileMenu,
  onOpenCommandPalette,
  onOpenShortcuts,
  resolvedTheme,
  onToggleTheme,
  transportMode = 'rest',
  onTransportModeChange,
}) {
  const [seconds, setSeconds] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setSeconds((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const formatDuration = (totalSec) => {
    const mins = Math.floor(totalSec / 60);
    const secs = totalSec % 60;
    return `${mins}m ${secs < 10 ? '0' : ''}${secs}s`;
  };

  return (
    <header
      className="min-h-[4.25rem] py-2.5 px-4 sm:px-6 lg:px-8 tf-panel flex flex-wrap items-center justify-between gap-3 sticky top-0 z-20"
      style={{ borderBottom: '1px solid var(--border-subtle)' }}
    >
      <div className="flex items-center gap-3 min-w-0">
        <button
          type="button"
          onClick={onToggleMobileMenu}
          className="tf-btn-target p-2 rounded-xl tf-subsurface tf-text-primary lg:hidden shrink-0 cursor-pointer"
          aria-label="Toggle navigation menu"
        >
          <Menu className="w-5 h-5" aria-hidden="true" />
        </button>

        <div className="min-w-0">
          <h1 className="text-base sm:text-lg font-bold tf-text-primary tracking-tight leading-snug truncate">
            Intelligent Context Engineering Workstation
          </h1>
          <p className="text-[11px] sm:text-xs tf-text-secondary truncate">
            RRF + MMR Ranking • HyDE RAG • Knapsack Token Budget • Injection Firewall • Circuit Breaker
          </p>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        {/* Command Palette Trigger */}
        <button
          type="button"
          onClick={onOpenCommandPalette}
          className="tf-btn-target flex items-center gap-2 px-3 py-1.5 rounded-xl tf-subsurface text-xs tf-text-secondary hover:opacity-90 cursor-pointer"
        >
          <Search className="w-3.5 h-3.5" aria-hidden="true" />
          <span className="hidden sm:inline font-medium">Commands</span>
          <kbd className="px-1.5 py-0.5 text-[10px] font-mono rounded tf-card tf-text-muted">⌘K</kbd>
        </button>

        {/* Tri-Mode Transport Segmented Radio Control (REST / WebSocket / SSE) */}
        <fieldset className="flex items-center gap-0.5 p-0.5 rounded-xl tf-subsurface">
          <legend className="visually-hidden">Execution Transport Protocol</legend>
          <Radio className="w-3.5 h-3.5 text-cyan-500 ml-2 mr-1 shrink-0 hidden sm:inline" aria-hidden="true" />
          {TRANSPORTS.map((mode) => {
            const active = transportMode === mode.id;
            return (
              <label
                key={mode.id}
                className={`px-2 py-1 rounded-lg text-[10px] font-mono font-bold cursor-pointer transition-colors ${
                  active
                    ? 'bg-cyan-500/20 text-cyan-500 border border-cyan-500/35'
                    : 'tf-text-muted border border-transparent hover:tf-text-primary'
                }`}
              >
                <input
                  type="radio"
                  name="transport_mode"
                  value={mode.id}
                  checked={active}
                  onChange={() => onTransportModeChange(mode.id)}
                  className="sr-only"
                />
                <span>{mode.label}</span>
              </label>
            );
          })}
        </fieldset>

        {/* Quick Theme Toggle */}
        <button
          type="button"
          onClick={onToggleTheme}
          className="tf-btn-target p-2 rounded-xl tf-subsurface tf-text-primary hover:opacity-85 cursor-pointer"
          aria-label={resolvedTheme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'}
        >
          {resolvedTheme === 'dark' ? (
            <Sun className="w-4 h-4 text-amber-400" aria-hidden="true" />
          ) : (
            <Moon className="w-4 h-4 text-indigo-600" aria-hidden="true" />
          )}
        </button>

        {/* Keyboard Shortcuts Trigger */}
        <button
          type="button"
          onClick={onOpenShortcuts}
          className="tf-btn-target p-2 rounded-xl tf-subsurface tf-text-secondary hover:opacity-85 hidden sm:inline-flex items-center justify-center cursor-pointer"
          aria-label="Keyboard shortcuts guide"
        >
          <Keyboard className="w-4 h-4" aria-hidden="true" />
        </button>

        {/* Active Pipeline Badge */}
        <div className="hidden xl:flex items-center gap-1.5 px-2.5 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/25 text-emerald-500 text-[11px] font-mono font-semibold">
          <Sparkles className="w-3.5 h-3.5 tf-spin-slow shrink-0" aria-hidden="true" />
          <span>Stateless Engine</span>
        </div>

        {/* Session Uptime */}
        <div className="hidden md:flex items-center gap-1.5 text-[11px] font-mono tf-text-secondary px-2.5 py-1.5 rounded-xl tf-subsurface shrink-0">
          <Clock className="w-3.5 h-3.5 tf-text-muted shrink-0" aria-hidden="true" />
          <span>{formatDuration(seconds)}</span>
        </div>

        {/* Reset Telemetry Button */}
        <button
          type="button"
          onClick={onResetStats}
          disabled={isResetting}
          className="tf-btn-target flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-500 border border-rose-500/30 text-xs font-semibold transition-all active:scale-95 disabled:opacity-50 cursor-pointer"
        >
          <RotateCcw className={`w-3.5 h-3.5 ${isResetting ? 'animate-spin' : ''}`} aria-hidden="true" />
          <span>Reset</span>
        </button>
      </div>
    </header>
  );
}
