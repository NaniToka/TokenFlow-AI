import React, { useEffect, useRef } from 'react';
import { AlertTriangle, CheckCircle2, Info, X } from 'lucide-react';

/**
 * Single Popover-backed toast card using popover="manual".
 * Automatically pauses dismissal timers when hovered or focused inside.
 */
function ToastItem({ toast, onDismiss }) {
  const ref = useRef(null);
  const isPausedRef = useRef(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    if (typeof el.showPopover === 'function') {
      try {
        if (!el.matches(':popover-open')) {
          el.showPopover();
        }
      } catch {
        // Fallback when element isn't connected in test environments
      }
    } else {
      el.classList.add(':popover-open');
    }

    if (typeof document.ariaNotify === 'function') {
      document.ariaNotify(toast.message);
    }
  }, [toast.message]);

  useEffect(() => {
    if (toast.type === 'error' || toast.persistent) return undefined;

    const timer = setInterval(() => {
      if (!isPausedRef.current) {
        onDismiss(toast.id);
      }
    }, 4500);

    return () => clearInterval(timer);
  }, [toast.id, toast.type, toast.persistent, onDismiss]);

  const styleMap = {
    error: 'bg-rose-950/95 text-rose-100 border-rose-500/45',
    warning: 'bg-amber-950/95 text-amber-100 border-amber-500/45',
    success: 'bg-emerald-950/95 text-emerald-100 border-emerald-500/45',
  };

  const Icon = toast.type === 'error' ? AlertTriangle : toast.type === 'warning' ? Info : CheckCircle2;

  return (
    <div
      ref={ref}
      id={`tf-toast-${toast.id}`}
      popover="manual"
      onMouseEnter={() => {
        isPausedRef.current = true;
      }}
      onMouseLeave={() => {
        isPausedRef.current = false;
      }}
      onFocus={() => {
        isPausedRef.current = true;
      }}
      onBlur={() => {
        isPausedRef.current = false;
      }}
      className={`tf-toast-popover flex items-center justify-between gap-3 px-3.5 py-2.5 border text-xs font-semibold backdrop-blur-xl ${
        styleMap[toast.type] || styleMap.success
      }`}
    >
      <div className="flex items-center gap-2.5 min-w-0">
        <Icon className="w-4 h-4 shrink-0" aria-hidden="true" />
        <span className="break-words leading-snug">{toast.message}</span>
      </div>
      <button
        type="button"
        popoverTarget={`tf-toast-${toast.id}`}
        popoverTargetAction="hide"
        onClick={() => onDismiss(toast.id)}
        aria-label="Dismiss notification"
        className="tf-btn-target p-1 rounded-lg hover:bg-white/10 shrink-0 cursor-pointer"
      >
        <X className="w-3.5 h-3.5" aria-hidden="true" />
      </button>
    </div>
  );
}

/**
 * Centralized accessible notification stack.
 * Combines a permanent `role="region"` landmark with an `aria-live="polite"` fallback
 * for browsers without `document.ariaNotify()`.
 */
export default function ToastRegion({ toasts = [], onDismiss }) {
  const latestMessage = toasts.length > 0 ? toasts[toasts.length - 1].message : '';

  return (
    <>
      <div aria-live="polite" className="visually-hidden">
        {latestMessage}
      </div>
      <div role="region" aria-label="Notifications" className="tf-toast-region">
        {toasts.map((t) => (
          <ToastItem key={t.id} toast={t} onDismiss={onDismiss} />
        ))}
      </div>
    </>
  );
}
