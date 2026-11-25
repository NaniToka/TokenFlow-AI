import React, { useState, useEffect, useCallback } from 'react';
import Sidebar from './components/layout/Sidebar';
import Header from './components/layout/Header';
import StatsOverview from './components/dashboard/StatsOverview';
import CompressionVisualizer from './components/dashboard/CompressionVisualizer';
import AnalyticsCharts from './components/dashboard/AnalyticsCharts';
import DemoModeSelector from './components/dashboard/DemoModeSelector';
import CustomInputForm from './components/dashboard/CustomInputForm';
import ConversationPlayground from './components/dashboard/ConversationPlayground';
import RagWorkbench from './components/dashboard/RagWorkbench';
import QualityEvaluator from './components/dashboard/QualityEvaluator';
import SystemSettings from './components/dashboard/SystemSettings';
import CommandPalette from './components/common/CommandPalette';
import ShortcutsModal from './components/common/ShortcutsModal';
import {
  getStats,
  resetStats,
  compressPrompt,
  getHealth,
  streamCompressWS,
} from './services/api';
import { DEMO_PRESETS } from './data/demoConversation';
import { useTheme } from './hooks/useTheme';
import { AlertTriangle, CheckCircle2, Code2, Sliders } from 'lucide-react';

export default function App() {
  const { preference, resolvedTheme, systemTheme, setPreference, toggleQuick } = useTheme();

  const [activeTab, setActiveTab] = useState('optimizer');
  const [isBackendConnected, setIsBackendConnected] = useState(true);
  const [llmAvailable, setLlmAvailable] = useState(false);
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  // Dialog states
  const [isCmdOpen, setIsCmdOpen] = useState(false);
  const [isShortcutsOpen, setIsShortcutsOpen] = useState(false);

  // Stats
  const [stats, setStats] = useState({
    total_requests: 0,
    total_original_tokens: 0,
    total_compressed_tokens: 0,
    total_tokens_saved: 0,
    total_cost_before_usd: 0,
    total_cost_after_usd: 0,
    total_cost_saved_usd: 0,
    avg_compression_ratio: 0,
    avg_latency_ms: 0,
    request_history: [],
  });

  // Optimizer & Strategy State
  const [selectedPresetId, setSelectedPresetId] = useState(DEMO_PRESETS[0].id);
  const [customQuery, setCustomQuery] = useState(DEMO_PRESETS[0].current_message);
  const [activeHistory, setActiveHistory] = useState(DEMO_PRESETS[0].history);
  const [topK, setTopK] = useState(3);
  const [targetModel, setTargetModel] = useState('gemini-1.5-flash');
  const [compressionMode, setCompressionMode] = useState('balanced');
  const [alphaOverride, setAlphaOverride] = useState(null);
  const [sanitizePii, setSanitizePii] = useState(false);
  const [useCache, setUseCache] = useState(true);
  const [useWebSocket, setUseWebSocket] = useState(false);

  const [inputMode, setInputMode] = useState('demo');
  const [rawHistoryJson, setRawHistoryJson] = useState('');

  // Execution & Live Feedback State
  const [isCompressing, setIsCompressing] = useState(false);
  const [wsStage, setWsStage] = useState(null);
  const [compressionResult, setCompressionResult] = useState(null);
  const [isResetting, setIsResetting] = useState(false);
  const [toastMessage, setToastMessage] = useState(null);

  const showToast = useCallback((message, type = 'success') => {
    setToastMessage({ message, type });
    setTimeout(() => setToastMessage(null), 4000);
  }, []);

  const fetchSessionStats = useCallback(async () => {
    try {
      const [statsData, healthData] = await Promise.all([getStats(), getHealth()]);
      setStats(statsData);
      setLlmAvailable(Boolean(healthData?.llm_available));
      setIsBackendConnected(true);
    } catch {
      setIsBackendConnected(false);
    }
  }, []);

  useEffect(() => {
    fetchSessionStats();
    const interval = setInterval(fetchSessionStats, 5000);
    return () => clearInterval(interval);
  }, [fetchSessionStats]);

  const handleSelectPreset = (presetId) => {
    setSelectedPresetId(presetId);
    const preset = DEMO_PRESETS.find((p) => p.id === presetId);
    if (preset) {
      setCustomQuery(preset.current_message);
      setActiveHistory([...preset.history]);
      setTopK(preset.top_k || preset.topK || 3);
      setCompressionResult(null);
      setWsStage(null);
    }
  };

  const handleRunCompression = useCallback(async (overrideHistory, overrideQuery) => {
    setIsCompressing(true);
    setWsStage(null);
    const historyToSend = overrideHistory ? [...overrideHistory] : [...activeHistory];
    const queryToSend = overrideQuery || customQuery;

    const payload = {
      history: historyToSend,
      current_message: queryToSend,
      top_k: Number(topK),
      alpha: alphaOverride,
      target_model: targetModel,
      compression_mode: compressionMode,
      sanitize_pii: sanitizePii,
      use_cache: useCache,
    };

    try {
      let result;
      if (useWebSocket) {
        result = await streamCompressWS(payload, (stageEvent) => {
          setWsStage(stageEvent);
        });
      } else {
        result = await compressPrompt(payload);
      }

      setCompressionResult(result);
      setActiveHistory(historyToSend);
      if (overrideQuery) setCustomQuery(overrideQuery);
      await fetchSessionStats();
      showToast(
        `Compressed: saved ${result.tokens_saved} tokens (${result.compression_ratio}%) in ${result.metadata?.latency_ms || 0}ms`
      );
    } catch (error) {
      showToast(
        error.response?.data?.detail || error.message || 'Backend connection failed.',
        'error'
      );
    } finally {
      setIsCompressing(false);
    }
  }, [activeHistory, customQuery, topK, alphaOverride, targetModel, compressionMode, sanitizePii, useCache, useWebSocket, fetchSessionStats, showToast]);

  // Global keyboard shortcuts (Cmd+K, Ctrl+Enter, Shift+?)
  useEffect(() => {
    const onKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setIsCmdOpen((prev) => !prev);
      } else if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
        e.preventDefault();
        handleRunCompression();
      } else if (e.key === '?' && !['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement?.tagName)) {
        e.preventDefault();
        setIsShortcutsOpen(true);
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [handleRunCompression]);

  const handleReset = async () => {
    setIsResetting(true);
    try {
      await resetStats();
      setCompressionResult(null);
      setWsStage(null);
      await fetchSessionStats();
      showToast('Session statistics reset.');
    } catch {
      showToast('Failed to reset session stats.', 'error');
    } finally {
      setIsResetting(false);
    }
  };

  return (
    <div className="flex min-h-dvh workstation-grid-bg relative overflow-x-hidden">
      {/* Skip to main content landmark link */}
      <a href="#main-content" className="skip-link visually-hidden">
        Skip to main content
      </a>

      {/* Single centralized polite live region for toast status notifications */}
      <div aria-live="polite" className="fixed bottom-4 right-4 sm:bottom-6 sm:right-6 z-50 max-w-[calc(100vw-2rem)]">
        {toastMessage && (
          <div
            className={`flex items-center gap-3 px-4 py-3 rounded-xl border text-xs font-semibold shadow-2xl backdrop-blur-xl ${
              toastMessage.type === 'error'
                ? 'bg-rose-950/95 text-rose-200 border-rose-500/40'
                : 'bg-emerald-950/95 text-emerald-200 border-emerald-500/40'
            }`}
          >
            {toastMessage.type === 'error' ? (
              <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" aria-hidden="true" />
            ) : (
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" aria-hidden="true" />
            )}
            <span className="truncate">{toastMessage.message}</span>
          </div>
        )}
      </div>

      {/* Native <dialog> Modals */}
      <CommandPalette
        isOpen={isCmdOpen}
        onClose={() => setIsCmdOpen(false)}
        onNavigate={setActiveTab}
        onRunCompression={() => handleRunCompression()}
        onToggleTheme={toggleQuick}
        presets={DEMO_PRESETS}
        onSelectPreset={handleSelectPreset}
      />

      <ShortcutsModal
        isOpen={isShortcutsOpen}
        onClose={() => setIsShortcutsOpen(false)}
      />

      {/* Responsive Navigation Sidebar */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        isBackendConnected={isBackendConnected}
        llmAvailable={llmAvailable}
        isMobileOpen={isMobileOpen}
        setIsMobileOpen={setIsMobileOpen}
      />

      <div className="flex-1 flex flex-col min-w-0">
        <Header
          onResetStats={handleReset}
          isResetting={isResetting}
          onToggleMobileMenu={() => setIsMobileOpen((prev) => !prev)}
          onOpenCommandPalette={() => setIsCmdOpen(true)}
          onOpenShortcuts={() => setIsShortcutsOpen(true)}
          resolvedTheme={resolvedTheme}
          onToggleTheme={toggleQuick}
          useWebSocket={useWebSocket}
          onToggleWebSocket={() => setUseWebSocket((prev) => !prev)}
        />

        <main id="main-content" tabIndex={-1} className="flex-1 p-3 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto space-y-6 min-w-0 outline-none">
          <StatsOverview stats={stats} targetModel={targetModel} />

          {activeTab === 'optimizer' && (
            <div className="space-y-6 min-w-0">
              <div className="flex items-center justify-between min-w-0">
                <div className="flex flex-wrap items-center gap-1.5 tf-subsurface p-1 rounded-xl w-full sm:w-auto">
                  <button
                    type="button"
                    onClick={() => setInputMode('demo')}
                    className={`tf-btn-target flex items-center justify-center gap-2 px-4 py-2 text-xs font-semibold rounded-lg transition-all flex-1 sm:flex-initial cursor-pointer ${
                      inputMode === 'demo'
                        ? 'bg-emerald-500/20 text-emerald-500 border border-emerald-500/35'
                        : 'tf-text-secondary hover:opacity-85'
                    }`}
                  >
                    <Sliders className="w-3.5 h-3.5" aria-hidden="true" /> Built-in Scenarios
                  </button>
                  <button
                    type="button"
                    onClick={() => setInputMode('manual')}
                    className={`tf-btn-target flex items-center justify-center gap-2 px-4 py-2 text-xs font-semibold rounded-lg transition-all flex-1 sm:flex-initial cursor-pointer ${
                      inputMode === 'manual'
                        ? 'bg-emerald-500/20 text-emerald-500 border border-emerald-500/35'
                        : 'tf-text-secondary hover:opacity-85'
                    }`}
                  >
                    <Code2 className="w-3.5 h-3.5" aria-hidden="true" /> Custom JSON Prompt
                  </button>
                </div>
              </div>

              {inputMode === 'demo' ? (
                <DemoModeSelector
                  selectedPresetId={selectedPresetId}
                  onSelectPreset={handleSelectPreset}
                  topK={topK}
                  onTopKChange={setTopK}
                  targetModel={targetModel}
                  onTargetModelChange={setTargetModel}
                  compressionMode={compressionMode}
                  onCompressionModeChange={setCompressionMode}
                  alphaOverride={alphaOverride}
                  onAlphaOverrideChange={setAlphaOverride}
                  sanitizePii={sanitizePii}
                  onSanitizePiiChange={setSanitizePii}
                  useCache={useCache}
                  onUseCacheChange={setUseCache}
                  onRunCompression={() => handleRunCompression()}
                  isCompressing={isCompressing}
                />
              ) : (
                <CustomInputForm
                  customQuery={customQuery}
                  onQueryChange={setCustomQuery}
                  rawHistoryJson={rawHistoryJson}
                  onRawHistoryChange={setRawHistoryJson}
                  sanitizePii={sanitizePii}
                  onSanitizePiiChange={setSanitizePii}
                  onExecuteCompression={(parsedHistory, query) => handleRunCompression(parsedHistory, query)}
                  isCompressing={isCompressing}
                />
              )}

              <CompressionVisualizer
                compressionResult={compressionResult}
                rawHistory={activeHistory}
                currentMessage={customQuery}
                wsStage={wsStage}
              />
            </div>
          )}

          {activeTab === 'playground' && (
            <div className="space-y-6">
              <ConversationPlayground
                history={activeHistory}
                onHistoryChange={setActiveHistory}
                query={customQuery}
                onQueryChange={setCustomQuery}
                onRunCompression={handleRunCompression}
                isCompressing={isCompressing}
              />
              {compressionResult && (
                <CompressionVisualizer
                  compressionResult={compressionResult}
                  rawHistory={activeHistory}
                  currentMessage={customQuery}
                  wsStage={wsStage}
                />
              )}
            </div>
          )}

          {activeTab === 'rag' && <RagWorkbench onToast={showToast} />}

          {activeTab === 'evaluator' && (
            <QualityEvaluator
              activeHistory={activeHistory}
              currentQuery={customQuery}
              compressionResult={compressionResult}
              onToast={showToast}
            />
          )}

          {activeTab === 'analytics' && <AnalyticsCharts stats={stats} onToast={showToast} />}

          {activeTab === 'settings' && (
            <SystemSettings
              themePreference={preference}
              systemTheme={systemTheme}
              onSetTheme={setPreference}
              targetModel={targetModel}
              compressionMode={compressionMode}
              topK={topK}
            />
          )}
        </main>
      </div>
    </div>
  );
}
