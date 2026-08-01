import React from 'react';

export default function Card({ title, subtitle, action, children, className = '' }) {
  return (
    <div className={`glass-card rounded-2xl p-6 relative overflow-hidden ${className}`}>
      {(title || action) && (
        <div className="flex items-center justify-between mb-4 border-b border-white/5 pb-3">
          <div>
            {title && <h3 className="text-lg font-semibold text-zinc-100 tracking-tight">{title}</h3>}
            {subtitle && <p className="text-xs text-zinc-400 mt-0.5">{subtitle}</p>}
          </div>
          {action && <div>{action}</div>}
        </div>
      )}
      {children}
    </div>
  );
}
