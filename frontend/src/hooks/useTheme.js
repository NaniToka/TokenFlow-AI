import { useState, useEffect, useCallback } from 'react';

const STORAGE_KEY = 'color-scheme';

function getStoredPreference() {
  try {
    const val = localStorage.getItem(STORAGE_KEY);
    return val === 'light' || val === 'dark' ? val : 'system';
  } catch {
    return 'system';
  }
}

function getSystemIsDark() {
  if (typeof window === 'undefined' || !window.matchMedia) return true;
  return window.matchMedia('(prefers-color-scheme: dark)').matches;
}

function applyMetaContent(pref) {
  const meta = document.querySelector('meta[name="color-scheme"]');
  if (meta) {
    meta.setAttribute('content', pref === 'system' ? 'light dark' : pref);
  }
}

/**
 * Tri-state color-scheme hook following modern-web-guidance dark-mode-toggle:
 * - 'system' removes localStorage key and sets <meta content="light dark">
 * - 'light' / 'dark' stores literal value and updates <meta>
 * - Listens to both media query changes and cross-tab storage events
 */
export function useTheme() {
  const [preference, setPreference] = useState(getStoredPreference);
  const [systemDark, setSystemDark] = useState(getSystemIsDark);

  const resolvedTheme = preference === 'system' ? (systemDark ? 'dark' : 'light') : preference;

  const updatePreference = useCallback((nextPref) => {
    const normalized = nextPref === 'light' || nextPref === 'dark' ? nextPref : 'system';
    setPreference(normalized);
    applyMetaContent(normalized);
    try {
      if (normalized === 'system') {
        localStorage.removeItem(STORAGE_KEY);
      } else {
        localStorage.setItem(STORAGE_KEY, normalized);
      }
    } catch {
      // Ignore storage quota / privacy mode errors
    }
  }, []);

  // Two-state quick toggle that respects system reversion semantics
  const toggleQuick = useCallback(() => {
    const target = resolvedTheme === 'dark' ? 'light' : 'dark';
    const currentSys = getSystemIsDark() ? 'dark' : 'light';
    if (target === currentSys) {
      updatePreference('system');
    } else {
      updatePreference(target);
    }
  }, [resolvedTheme, updatePreference]);

  useEffect(() => {
    applyMetaContent(preference);
  }, [preference]);

  useEffect(() => {
    const mql = window.matchMedia('(prefers-color-scheme: dark)');
    const onMediaChange = (e) => setSystemDark(e.matches);
    const onStorageChange = (e) => {
      if (e.key === STORAGE_KEY) {
        const next = e.newValue === 'light' || e.newValue === 'dark' ? e.newValue : 'system';
        setPreference(next);
        applyMetaContent(next);
      }
    };

    mql.addEventListener('change', onMediaChange);
    window.addEventListener('storage', onStorageChange);
    return () => {
      mql.removeEventListener('change', onMediaChange);
      window.removeEventListener('storage', onStorageChange);
    };
  }, []);

  return {
    preference,
    resolvedTheme,
    systemTheme: systemDark ? 'dark' : 'light',
    setPreference: updatePreference,
    toggleQuick,
  };
}
