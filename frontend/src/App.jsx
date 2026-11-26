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
import ExperimentsStudio from './components/dashboard/ExperimentsStudio';
import QualityEvaluator from './components/dashboard/QualityEvaluator';
import SecurityFirewall from './components/dashboard/SecurityFirewall';
import TraceConsole from './components/dashboard/TraceConsole';
import SystemSettings from './components/dashboard/SystemSettings';
import CommandPalette from './components/common/CommandPalette';
import ShortcutsModal from './components/common/ShortcutsModal';
import ToastRegion from './components/common/ToastRegion';
import {
  getStats,
  resetStats,
  compressPrompt,
  getHealth,
  streamCompressWS,
  streamCompressSSE,
} from './services/api';
import { DEMO_PRESETS } from './data/demoConversation';
import { useTheme } from './hooks/useTheme';
import { Code2, Sliders } from 'lucide-react';

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
  const [fusionMethod, setFusionMethod] = useState('rrf');
  const [useMmr, setUseMmr] = useState(true);
  const [useReranker, setUseReranker] = useState(true);
  const [useDedup, setUseDedup] = useState(true);
  const [maxContextTokens, setMaxContextTokens] = useState(null);
  const [alphaOverride, setAlphaOverride] = useState(null);
  const [sanitizePii, setSanitizePii] = useState(false);
  const [useCache, setUseCache] = useState(true);
  const [transportMode, setTransportMode] = useState('rest'); // 'rest' | 'ws' | 'sse'

  const [inputMode, setInputMode] = useState('demo');
  const [rawHistoryJson, setRawHistoryJson] = useState('');

  // Execution & Live Feedback State
  const [isCompressing, setIsCompressing] = useState(false);
  const [wsStage, setWsStage] = useState(null);
  const [compressionResult, setCompressionResult] = useState(null);
  const [isResetting, setIsResetting] = useState(false);
  const [toasts, setToasts] = useState([]);

  const dismissToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const showToast = useCallback((message, type = 'success') => {
    const id = `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
    setToasts((prev) => [...prev.slice(-2), { id, message, type }]);
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
      fusion_method: fusionMethod,
      use_mmr: useMmr,
      use_reranker: useReranker,
      use_dedup: useDedup,
      max_context_tokens: maxContextTokens,
      sanitize_pii: sanitizePii,
      use_cache: useCache,
    };

    try {
      let result;
      if (transportMode === 'ws') {
        result = await streamCompressWS(payload, (stageEvent) => {
          setWsStage(stageEvent);
        });
      } else if (transportMode === 'sse') {
        result = await streamCompressSSE(payload, (stageEvent) => {
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
  }, [
    activeHistory,
    customQuery,
    topK,
    alphaOverride,
    targetModel,
    compressionMode,
    fusionMethod,
    useMmr,
    useReranker,
    useDedup,
    maxContextTokens,
    sanitizePii,
    useCache,
    transportMode,
    fetchSessionStats,
    showToast,
  ]);

  // Global keyboard shortcuts (IME composition safe)
  useEffect(() => {
    const onKeyDown = (e) => {
      if (e.isComposing) return;
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

      {/* Accessible popover="manual" persistent toast region */}
      <ToastRegion toasts={toasts} onDismiss={dismissToast} />

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
          transportMode={transportMode}
          onTransportModeChange={setTransportMode}
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
                  fusionMethod={fusionMethod}
                  onFusionMethodChange={setFusionMethod}
                  useMmr={useMmr}
                  onUseMmrChange={setUseMmr}
                  useReranker={useReranker}
                  onUseRerankerChange={setUseReranker}
                  useDedup={useDedup}
                  onUseDedupChange={setUseDedup}
                  maxContextTokens={maxContextTokens}
                  onMaxContextTokensChange={setMaxContextTokens}
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
                maxContextTokens={maxContextTokens}
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
                  maxContextTokens={maxContextTokens}
                  wsStage={wsStage}
                />
              )}
            </div>
          )}

          {activeTab === 'rag' && <RagWorkbench onToast={showToast} />}

          {activeTab === 'experiments' && (
            <ExperimentsStudio
              activeHistory={activeHistory}
              currentQuery={customQuery}
              onToast={showToast}
            />
          )}

          {activeTab === 'evaluator' && (
            <QualityEvaluator
              activeHistory={activeHistory}
              currentQuery={customQuery}
              compressionResult={compressionResult}
              onToast={showToast}
            />
          )}

          {activeTab === 'firewall' && <SecurityFirewall onToast={showToast} />}

          {activeTab === 'analytics' && <AnalyticsCharts stats={stats} onToast={showToast} />}

          {activeTab === 'logs' && <TraceConsole onToast={showToast} />}

          {activeTab === 'settings' && (
            <SystemSettings
              themePreference={preference}
              systemTheme={systemTheme}
              onSetTheme={setPreference}
              targetModel={targetModel}
              compressionMode={compressionMode}
              topK={topK}
              fusionMethod={fusionMethod}
              sanitizePii={sanitizePii}
            />
          )}
        </main>
      </div>
    </div>
  );
}
