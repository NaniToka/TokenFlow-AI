import React from 'react';

export default function MetricCard({
  title,
  value,
  subtitle,
  icon: Icon,
  badgeText,
  badgeType = 'emerald', // emerald, cyan, violet, rose
  glowColor = 'emerald'
}) {
  const badgeStyles = {
    emerald: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
    cyan: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30',
    violet: 'bg-violet-500/10 text-violet-400 border-violet-500/30',
    rose: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
  };

  const iconStyles = {
    emerald: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
    cyan: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/20',
    violet: 'text-violet-400 bg-violet-500/10 border-violet-500/20',
    rose: 'text-rose-400 bg-rose-500/10 border-rose-500/20',
  };

  const glowStyles = {
    emerald: 'glow-emerald',
    cyan: 'glow-cyan',
    violet: 'glow-violet',
    rose: '',
  };

  return (
    <div className={`glass-card rounded-2xl p-4 sm:p-5 relative overflow-hidden min-w-0 transition-all duration-300 ${glowStyles[glowColor] || ''}`}>
      <div className="flex items-center justify-between mb-2 sm:mb-3 gap-2">
        <span className="text-[11px] sm:text-xs font-semibold uppercase tracking-wider text-zinc-400 truncate">{title}</span>
        {Icon && (
          <div className={`w-8 h-8 sm:w-9 sm:h-9 rounded-xl flex items-center justify-center border shrink-0 ${iconStyles[badgeType]}`}>
            <Icon className="w-4 h-4 sm:w-5 sm:h-5" />
          </div>
        )}
      </div>

      <div className="flex items-baseline justify-between mt-1 gap-2">
        <h3 className="text-xl sm:text-2xl font-bold text-zinc-100 tracking-tight truncate">{value}</h3>
        {badgeText && (
          <span className={`text-[10px] sm:text-[11px] font-semibold px-2 py-0.5 rounded-full border shrink-0 ${badgeStyles[badgeType]}`}>
            {badgeText}
          </span>
        )}
      </div>

      {subtitle && <p className="text-[11px] sm:text-xs text-zinc-500 mt-2 font-medium truncate">{subtitle}</p>}
    </div>
  );
}
