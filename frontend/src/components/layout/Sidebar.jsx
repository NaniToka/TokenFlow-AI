import React from 'react';
import { Cpu, BarChart3, Sliders, Settings, Zap, CheckCircle2, XCircle, X } from 'lucide-react';

export default function Sidebar({
  activeTab,
  setActiveTab,
  isBackendConnected = true,
  isMobileOpen = false,
  setIsMobileOpen
}) {
  const navItems = [
    { id: 'optimizer', label: 'Prompt Optimizer', icon: Cpu },
    { id: 'analytics', label: 'Live Analytics', icon: BarChart3 },
    { id: 'demo', label: 'Demo Scenarios', icon: Sliders },
    { id: 'settings', label: 'API Settings', icon: Settings },
  ];

  const handleTabClick = (id) => {
    setActiveTab(id);
    if (setIsMobileOpen) {
      setIsMobileOpen(false);
    }
  };

  return (
    <>
      {/* Mobile Drawer Backdrop */}
      {isMobileOpen && (
        <div
          onClick={() => setIsMobileOpen && setIsMobileOpen(false)}
          className="fixed inset-0 bg-black/80 backdrop-blur-sm z-40 lg:hidden transition-opacity"
        />
      )}

      <aside
        className={`fixed lg:sticky top-0 left-0 bottom-0 z-50 lg:z-30 w-64 glass-panel border-r border-white/10 flex flex-col justify-between h-screen select-none transition-transform duration-300 ease-in-out ${
          isMobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        <div>
          {/* Brand Header */}
          <div className="p-5 sm:p-6 flex items-center justify-between border-b border-white/10">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-500 to-cyan-500 flex items-center justify-center shadow-lg shadow-emerald-500/20">
                <Zap className="w-5 h-5 text-zinc-950 stroke-[2.5]" />
              </div>
              <div>
                <h1 className="font-bold text-lg text-zinc-100 tracking-tight flex items-center gap-1.5">
                  TokenFlow <span className="text-xs px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-semibold border border-emerald-500/30">AI</span>
                </h1>
                <p className="text-[11px] text-zinc-400 font-medium">Memory Middleware</p>
              </div>
            </div>

            {/* Mobile Close Icon */}
            <button
              onClick={() => setIsMobileOpen && setIsMobileOpen(false)}
              className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-white/10 lg:hidden"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Navigation Tabs */}
          <nav className="p-4 space-y-1.5">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => handleTabClick(item.id)}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 ${
                    isActive
                      ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 shadow-md shadow-emerald-500/10'
                      : 'text-zinc-400 hover:text-zinc-200 hover:bg-white/5 border border-transparent'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-emerald-400' : 'text-zinc-400'}`} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Backend Status Footer */}
        <div className="p-4 border-t border-white/10">
          <div className="p-3 rounded-xl bg-zinc-950/60 border border-white/5 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              {isBackendConnected ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-400 animate-pulse" />
              ) : (
                <XCircle className="w-4 h-4 text-rose-400" />
              )}
              <div>
                <p className="text-xs font-semibold text-zinc-200">
                  {isBackendConnected ? 'Backend Connected' : 'Offline'}
                </p>
                <p className="text-[10px] text-zinc-500">FastAPI :8000</p>
              </div>
            </div>
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
          </div>
        </div>
      </aside>
    </>
  );
}
