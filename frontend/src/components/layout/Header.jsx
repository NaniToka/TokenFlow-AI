import React, { useState, useEffect } from 'react';
import { RotateCcw, Sparkles, Clock, Menu } from 'lucide-react';

export default function Header({ onResetStats, isResetting = false, onToggleMobileMenu }) {
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
    <header className="min-h-[4.5rem] py-3 sm:py-0 border-b border-white/10 bg-zinc-950/80 backdrop-blur-xl px-4 sm:px-8 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 sticky top-0 z-20">
      <div className="flex items-center gap-3 w-full sm:w-auto justify-between sm:justify-start">
        <div className="flex items-center gap-3">
          <button
            onClick={onToggleMobileMenu}
            className="p-2 rounded-xl bg-zinc-900 border border-zinc-800 text-zinc-300 hover:text-white lg:hidden shrink-0"
            aria-label="Toggle mobile menu"
          >
            <Menu className="w-5 h-5" />
          </button>
          <div>
            <h2 className="text-base sm:text-xl font-bold text-zinc-100 tracking-tight leading-snug">
              Prompt Memory Optimizer Dashboard
            </h2>
            <p className="text-[11px] sm:text-xs text-zinc-400">
              Real-time semantic ranking & context compression middleware
            </p>
          </div>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2 sm:gap-3 w-full sm:w-auto justify-between sm:justify-end">
        {/* Gemini Active Badge */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-gradient-to-r from-violet-500/10 to-indigo-500/10 border border-violet-500/30 text-violet-300 text-[11px] sm:text-xs font-medium truncate max-w-full">
          <Sparkles className="w-3.5 h-3.5 text-violet-400 animate-spin-slow shrink-0" />
          <span className="truncate">Gemini 1.5 Flash + text-embedding-004</span>
        </div>

        <div className="flex items-center gap-2">
          {/* Session Timer */}
          <div className="flex items-center gap-1.5 text-[11px] sm:text-xs text-zinc-400 px-2.5 py-1 rounded-xl bg-zinc-900/60 border border-white/5 shrink-0">
            <Clock className="w-3.5 h-3.5 text-zinc-500 shrink-0" />
            <span>{formatDuration(seconds)}</span>
          </div>

          {/* Reset Button */}
          <button
            onClick={onResetStats}
            disabled={isResetting}
            className="flex items-center gap-1.5 px-3 py-1 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 text-[11px] sm:text-xs font-semibold transition-all active:scale-95 disabled:opacity-50 shrink-0"
          >
            <RotateCcw className={`w-3.5 h-3.5 ${isResetting ? 'animate-spin' : ''}`} />
            <span>Reset</span>
          </button>
        </div>
      </div>
    </header>
  );
}
