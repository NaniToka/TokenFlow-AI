import React, { useState, useEffect } from 'react';
import { RotateCcw, Sparkles, Clock } from 'lucide-react';

export default function Header({ onResetStats, isResetting = false }) {
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
    <header className="h-20 border-b border-white/10 bg-zinc-950/80 backdrop-blur-xl px-8 flex items-center justify-between sticky top-0 z-20">
      <div>
        <h2 className="text-xl font-bold text-zinc-100 tracking-tight flex items-center gap-2">
          Prompt Memory Optimizer Dashboard
        </h2>
        <p className="text-xs text-zinc-400">
          Real-time semantic ranking & context compression middleware
        </p>
      </div>

      <div className="flex items-center gap-4">
        {/* Gemini Active Badge */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-gradient-to-r from-violet-500/10 to-indigo-500/10 border border-violet-500/30 text-violet-300 text-xs font-medium">
          <Sparkles className="w-3.5 h-3.5 text-violet-400 animate-spin-slow" />
          <span>Gemini 1.5 Flash + text-embedding-004</span>
        </div>

        {/* Session Timer */}
        <div className="flex items-center gap-1.5 text-xs text-zinc-400 px-3 py-1.5 rounded-xl bg-zinc-900/60 border border-white/5">
          <Clock className="w-3.5 h-3.5 text-zinc-500" />
          <span>Session: {formatDuration(seconds)}</span>
        </div>

        {/* Reset Button */}
        <button
          onClick={onResetStats}
          disabled={isResetting}
          className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 text-xs font-semibold transition-all active:scale-95 disabled:opacity-50"
        >
          <RotateCcw className={`w-3.5 h-3.5 ${isResetting ? 'animate-spin' : ''}`} />
          <span>Reset Session</span>
        </button>
      </div>
    </header>
  );
}
