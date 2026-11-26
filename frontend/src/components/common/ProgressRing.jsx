import React from 'react';

/**
 * Semantic circular progress gauge built on native <progress> + CSS conic-gradient.
 * Complies with modern-web-guidance `progress-ring`:
 * - Native <progress> for assistive technology semantics (no text children inside <progress>)
 * - aria-hidden="true" on duplicate center label to prevent double screen-reader announcement
 * - Uses aria-valuetext when custom descriptive text is shown
 */
export default function ProgressRing({
  value = 0,
  max = 100,
  label = 'Progress',
  displayValue,
  subLabel,
  size = 84,
  thickness = 8,
  color = 'var(--accent-primary)',
}) {
  const numericMax = Math.max(1, Number(max) || 100);
  const clamped = Math.min(numericMax, Math.max(0, Number(value) || 0));
  const pct = (clamped / numericMax) * 100;
  const shownText = displayValue !== undefined ? displayValue : `${Math.round(pct)}%`;

  return (
    <div className="tf-progress-ring-wrapper">
      <progress
        value={clamped}
        max={numericMax}
        aria-label={label}
        aria-valuetext={`${shownText}${subLabel ? ` ${subLabel}` : ''}`}
        className="tf-progress-ring"
        style={{
          '--size': `${size}px`,
          '--thickness': `${thickness}px`,
          '--value': pct,
          '--fill-color': color,
        }}
      />
      <div className="tf-progress-ring-content" aria-hidden="true">
        <span className="text-sm font-extrabold font-mono tf-text-primary leading-none">
          {shownText}
        </span>
        {subLabel && (
          <span className="text-[9px] font-mono uppercase tracking-wider tf-text-muted mt-0.5">
            {subLabel}
          </span>
        )}
      </div>
    </div>
  );
}
