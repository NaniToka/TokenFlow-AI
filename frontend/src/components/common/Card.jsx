import React from 'react';

export default function Card({ title, subtitle, action, children, className = '' }) {
  return (
    <div className={`glass-card rounded-2xl p-4 sm:p-6 relative overflow-hidden min-w-0 ${className}`}>
      {(title || action) && (
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-4 border-b border-white/5 pb-3 min-w-0">
          <div className="min-w-0">
            {title && <h3 className="text-base sm:text-lg font-semibold text-zinc-100 tracking-tight leading-snug truncate">{title}</h3>}
            {subtitle && <p className="text-[11px] sm:text-xs text-zinc-400 mt-0.5">{subtitle}</p>}
          </div>
          {action && <div className="shrink-0 w-full sm:w-auto">{action}</div>}
        </div>
      )}
      {children}
    </div>
  );
}
