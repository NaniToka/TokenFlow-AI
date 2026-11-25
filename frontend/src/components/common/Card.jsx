import React from 'react';

export default function Card({ title, subtitle, action, children, className = '' }) {
  return (
    <section className={`tf-card rounded-2xl p-4 sm:p-6 relative overflow-hidden min-w-0 ${className}`}>
      {(title || action) && (
        <div
          className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-4 pb-3 min-w-0"
          style={{ borderBottom: '1px solid var(--border-subtle)' }}
        >
          <div className="min-w-0">
            {title && (
              <h2 className="text-base sm:text-lg font-semibold tf-text-primary tracking-tight leading-snug truncate">
                {title}
              </h2>
            )}
            {subtitle && (
              <p className="text-xs tf-text-secondary mt-0.5">{subtitle}</p>
            )}
          </div>
          {action && <div className="shrink-0 w-full sm:w-auto">{action}</div>}
        </div>
      )}
      {children}
    </section>
  );
}
