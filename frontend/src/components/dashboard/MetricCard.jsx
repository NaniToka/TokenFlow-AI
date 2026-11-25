import React from 'react';

export default function MetricCard({
  title,
  value,
  subtitle,
  icon: Icon,
  badgeText,
  badgeType = 'emerald',
}) {
  const badgeStyles = {
    emerald: 'bg-emerald-500/10 text-emerald-500 border-emerald-500/30',
    cyan: 'bg-cyan-500/10 text-cyan-500 border-cyan-500/30',
    violet: 'bg-violet-500/10 text-violet-500 border-violet-500/30',
    rose: 'bg-rose-500/10 text-rose-500 border-rose-500/30',
  };

  const iconStyles = {
    emerald: 'text-emerald-500 bg-emerald-500/10 border-emerald-500/25',
    cyan: 'text-cyan-500 bg-cyan-500/10 border-cyan-500/25',
    violet: 'text-violet-500 bg-violet-500/10 border-violet-500/25',
    rose: 'text-rose-500 bg-rose-500/10 border-rose-500/25',
  };

  return (
    <article className="tf-card rounded-2xl p-4 sm:p-5 relative overflow-hidden min-w-0">
      <div className="flex items-center justify-between mb-2 sm:mb-3 gap-2">
        <span className="text-[11px] font-bold uppercase tracking-wider tf-text-muted truncate">
          {title}
        </span>
        {Icon && (
          <div className={`w-8 h-8 rounded-xl flex items-center justify-center border shrink-0 ${iconStyles[badgeType]}`}>
            <Icon className="w-4 h-4" aria-hidden="true" />
          </div>
        )}
      </div>

      <div className="flex items-baseline justify-between mt-1 gap-2">
        <p className="text-xl sm:text-2xl font-bold font-mono tf-text-primary tracking-tight truncate">
          {value}
        </p>
        {badgeText && (
          <span className={`text-[10px] sm:text-[11px] font-mono font-semibold px-2 py-0.5 rounded-full border shrink-0 ${badgeStyles[badgeType]}`}>
            {badgeText}
          </span>
        )}
      </div>

      {subtitle && (
        <p className="text-[11px] tf-text-secondary mt-2 font-medium truncate">
          {subtitle}
        </p>
      )}
    </article>
  );
}
