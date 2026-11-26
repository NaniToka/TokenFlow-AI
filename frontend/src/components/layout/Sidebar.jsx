import React from 'react';
import {
  Cpu,
  MessageSquareCode,
  BookOpen,
  FlaskConical,
  Target,
  BarChart3,
  ShieldAlert,
  Activity,
  Settings,
  Zap,
  CheckCircle2,
  XCircle,
  X,
} from 'lucide-react';

export default function Sidebar({
  activeTab,
  setActiveTab,
  isBackendConnected = true,
  llmAvailable = false,
  isMobileOpen = false,
  setIsMobileOpen,
}) {
  const navItems = [
    { id: 'optimizer', label: 'Context Workbench', badge: 'Core', icon: Cpu },
    { id: 'playground', label: 'Chat Playground', badge: 'Live', icon: MessageSquareCode },
    { id: 'rag', label: 'RAG Document Lab', badge: 'HyDE', icon: BookOpen },
    { id: 'experiments', label: 'A/B & Needle Lab', badge: 'Bench', icon: Target },
    { id: 'evaluator', label: 'Quality Judge', badge: 'Eval', icon: FlaskConical },
    { id: 'firewall', label: 'Prompt Firewall', badge: 'Guard', icon: ShieldAlert },
    { id: 'analytics', label: 'Telemetry & P95', badge: 'Ops', icon: BarChart3 },
    { id: 'logs', label: 'Live Trace Logs', badge: 'Ring', icon: Activity },
    { id: 'settings', label: 'SDK & Config', badge: 'v3 API', icon: Settings },
  ];

  const handleTabClick = (id) => {
    setActiveTab(id);
    if (setIsMobileOpen) {
      setIsMobileOpen(false);
    }
  };

  return (
    <>
      {isMobileOpen && (
        <div
          onClick={() => setIsMobileOpen && setIsMobileOpen(false)}
          className="fixed inset-0 bg-black/70 backdrop-blur-sm z-40 lg:hidden"
          aria-hidden="true"
        />
      )}

      <aside
        aria-label="Workstation Navigation"
        className={`fixed lg:sticky top-0 left-0 bottom-0 z-50 lg:z-30 w-64 tf-panel flex flex-col justify-between h-dvh transition-transform duration-300 ease-in-out ${
          isMobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
        style={{ borderRight: '1px solid var(--border-subtle)' }}
      >
        <div className="overflow-y-auto tf-scroller">
          {/* Brand Header */}
          <div
            className="p-4 sm:p-5 flex items-center justify-between"
            style={{ borderBottom: '1px solid var(--border-subtle)' }}
          >
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-500 to-cyan-500 flex items-center justify-center shadow-lg shadow-emerald-500/20">
                <Zap className="w-5 h-5 text-zinc-950 stroke-[2.5]" aria-hidden="true" />
              </div>
              <div>
                <div className="font-bold text-base tf-text-primary tracking-tight flex items-center gap-1.5">
                  TokenFlow{' '}
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/15 text-emerald-500 font-mono font-bold border border-emerald-500/30">
                    v3.0
                  </span>
                </div>
                <p className="text-[11px] tf-text-muted font-mono">Context Middleware</p>
              </div>
            </div>

            <button
              type="button"
              onClick={() => setIsMobileOpen && setIsMobileOpen(false)}
              aria-label="Close navigation drawer"
              className="tf-btn-target p-1.5 rounded-lg tf-text-secondary hover:bg-emerald-500/10 lg:hidden cursor-pointer"
            >
              <X className="w-5 h-5" aria-hidden="true" />
            </button>
          </div>

          {/* Primary Navigation */}
          <nav aria-label="Primary" className="p-3 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => handleTabClick(item.id)}
                  aria-current={isActive ? 'page' : undefined}
                  className={`tf-btn-target w-full flex items-center justify-between gap-2 px-3 py-2 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                    isActive
                      ? 'bg-emerald-500/15 text-emerald-500 border border-emerald-500/35 shadow-sm'
                      : 'tf-text-secondary hover:bg-emerald-500/5 border border-transparent'
                  }`}
                >
                  <span className="flex items-center gap-2.5 truncate">
                    <Icon
                      className="w-4 h-4 shrink-0"
                      style={{ color: isActive ? 'var(--accent-primary)' : undefined }}
                      aria-hidden="true"
                    />
                    <span className="truncate">{item.label}</span>
                  </span>
                  <span
                    className={`text-[9px] font-mono uppercase px-1.5 py-0.5 rounded ${
                      isActive ? 'bg-emerald-500/20 text-emerald-400' : 'tf-subsurface tf-text-muted'
                    }`}
                  >
                    {item.badge}
                  </span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Backend & Engine Diagnostics Footer */}
        <div className="p-3.5 space-y-2" style={{ borderTop: '1px solid var(--border-subtle)' }}>
          <div className="p-3 rounded-xl tf-subsurface space-y-2">
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-2 min-w-0">
                {isBackendConnected ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 tf-pulse" aria-hidden="true" />
                ) : (
                  <XCircle className="w-4 h-4 text-rose-500 shrink-0" aria-hidden="true" />
                )}
                <div className="min-w-0">
                  <p className="text-xs font-semibold tf-text-primary truncate">
                    {isBackendConnected ? 'Engine Online' : 'Backend Offline'}
                  </p>
                  <p className="text-[10px] font-mono tf-text-muted truncate">
                    {llmAvailable ? 'Gemini + RRF + MMR' : 'Offline RRF + Extractive'}
                  </p>
                </div>
              </div>
              <span
                className={`w-2 h-2 rounded-full shrink-0 ${
                  isBackendConnected ? 'bg-emerald-500' : 'bg-rose-500'
                }`}
                aria-hidden="true"
              />
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
