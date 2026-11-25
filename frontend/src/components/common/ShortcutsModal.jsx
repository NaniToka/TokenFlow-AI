import React, { useEffect, useRef } from 'react';
import { Keyboard, X } from 'lucide-react';

/**
 * Native <dialog closedby="any"> Keyboard Shortcuts Reference Modal
 */
export default function ShortcutsModal({ isOpen, onClose }) {
  const dialogRef = useRef(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    if (isOpen && !dialog.open) {
      dialog.showModal();
    } else if (!isOpen && dialog.open) {
      dialog.close();
    }
  }, [isOpen]);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    const handleClose = () => onClose();
    dialog.addEventListener('close', handleClose);

    if (!('closedBy' in HTMLDialogElement.prototype)) {
      let pressedOutside = false;
      const outside = (e) => {
        const r = dialog.getBoundingClientRect();
        return e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom;
      };
      const onDown = (e) => { pressedOutside = outside(e); };
      const onUp = (e) => { if (pressedOutside && outside(e)) dialog.close(); };
      dialog.addEventListener('pointerdown', onDown);
      dialog.addEventListener('pointerup', onUp);
      return () => {
        dialog.removeEventListener('close', handleClose);
        dialog.removeEventListener('pointerdown', onDown);
        dialog.removeEventListener('pointerup', onUp);
      };
    }

    return () => dialog.removeEventListener('close', handleClose);
  }, [onClose]);

  const shortcuts = [
    { keys: ['⌘ / Ctrl', 'K'], desc: 'Open Global Command Palette' },
    { keys: ['⌘ / Ctrl', 'Enter'], desc: 'Execute Prompt Compression' },
    { keys: ['Shift', '?'], desc: 'Open Keyboard Shortcuts Guide' },
    { keys: ['Esc'], desc: 'Dismiss Active Modal Dialog' },
    { keys: ['Tab'], desc: 'Navigate Workstation Landmarks' },
  ];

  return (
    <dialog
      ref={dialogRef}
      closedby="any"
      aria-labelledby="shortcuts-modal-title"
      className="tf-dialog"
    >
      <div className="p-5 sm:p-6 space-y-4">
        <div className="flex items-center justify-between gap-3 pb-3" style={{ borderBottom: '1px solid var(--border-subtle)' }}>
          <div className="flex items-center gap-2.5">
            <Keyboard className="w-5 h-5" style={{ color: 'var(--accent-primary)' }} aria-hidden="true" />
            <h1 id="shortcuts-modal-title" className="text-base font-bold tf-text-primary">
              Workstation Keyboard Shortcuts
            </h1>
          </div>
          <button
            type="button"
            autofocus
            onClick={() => dialogRef.current?.close()}
            aria-label="Close shortcuts dialog"
            className="tf-btn-target p-1.5 rounded-lg tf-subsurface tf-text-secondary cursor-pointer"
          >
            <X className="w-4 h-4" aria-hidden="true" />
          </button>
        </div>

        <ul className="space-y-2.5">
          {shortcuts.map((s) => (
            <li
              key={s.desc}
              className="flex items-center justify-between gap-4 p-2.5 rounded-xl tf-subsurface text-xs"
            >
              <span className="tf-text-primary font-medium">{s.desc}</span>
              <div className="flex items-center gap-1 shrink-0">
                {s.keys.map((k) => (
                  <kbd
                    key={k}
                    className="px-2 py-0.5 rounded font-mono text-[11px] font-bold tf-card"
                  >
                    {k}
                  </kbd>
                ))}
              </div>
            </li>
          ))}
        </ul>
      </div>
    </dialog>
  );
}
