import React, { useState, useEffect } from 'react';
import Sidebar from './components/layout/Sidebar';
import Header from './components/layout/Header';
import StatsOverview from './components/dashboard/StatsOverview';
import CompressionVisualizer from './components/dashboard/CompressionVisualizer';
import AnalyticsCharts from './components/dashboard/AnalyticsCharts';
import DemoModeSelector from './components/dashboard/DemoModeSelector';
import CustomInputForm from './components/dashboard/CustomInputForm';
import Card from './components/common/Card';
import { getStats, resetStats, compressPrompt } from './services/api';
import { DEMO_PRESETS } from './data/demoConversation';
import { AlertTriangle, CheckCircle2, Code2, Sliders } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('optimizer');
  const [isBackendConnected, setIsBackendConnected] = useState(true);
  const [stats, setStats] = useState({
    total_requests: 0,
    total_original_tokens: 0,
    total_compressed_tokens: 0,
    total_tokens_saved: 0,
    total_cost_before_usd: 0,
    total_cost_after_usd: 0,
    total_cost_saved_usd: 0,
    avg_compression_ratio: 0,
    request_history: []
  });

  // Demo & Custom Prompt State
  const [selectedPresetId, setSelectedPresetId] = useState('tech_architecture');
  const [customQuery, setCustomQuery] = useState(
    'How do I optimize the composite index for my Postgres query SELECT * FROM orders WHERE user_id = 42 AND status = "shipped" ORDER BY created_at DESC?'
  );
  const [topK, setTopK] = useState(3);
  const [inputMode, setInputMode] = useState('demo'); // 'demo' | 'manual'
  const [rawHistoryJson, setRawHistoryJson] = useState('');

  // Execution & UI Feedback State
  const [isCompressing, setIsCompressing] = useState(false);
  const [compressionResult, setCompressionResult] = useState(null);
  const [activeHistory, setActiveHistory] = useState(DEMO_PRESETS[0].history);
  const [isResetting, setIsResetting] = useState(false);
  const [toastMessage, setToastMessage] = useState(null);

  const fetchSessionStats = async () => {
    try {
      const data = await getStats();
      setStats(data);
      setIsBackendConnected(true);
    } catch (error) {
      console.error('Error fetching session stats:', error);
      setIsBackendConnected(false);
    }
  };

  useEffect(() => {
    fetchSessionStats();
    const interval = setInterval(fetchSessionStats, 4000);
    return () => clearInterval(interval);
  }, []);

  const showToast = (message, type = 'success') => {
    setToastMessage({ message, type });
    setTimeout(() => setToastMessage(null), 4000);
  };

  const handleSelectPreset = (presetId) => {
    setSelectedPresetId(presetId);
    const preset = DEMO_PRESETS.find((p) => p.id === presetId);
    if (preset) {
      setCustomQuery(preset.current_message);
      setActiveHistory([...preset.history]);
      setTopK(preset.top_k || 3);
      setCompressionResult(null); // Clear previous visualizer result on preset change
    }
  };

  const handleRunCompression = async (overrideHistory, overrideQuery) => {
    setIsCompressing(true);
    const historyToSend = overrideHistory ? [...overrideHistory] : [...activeHistory];
    const queryToSend = overrideQuery || customQuery;

    try {
      const payload = {
        history: historyToSend,
        current_message: queryToSend,
        top_k: Number(topK)
      };

      const result = await compressPrompt(payload);
      setCompressionResult(result);
      setActiveHistory(historyToSend);
      await fetchSessionStats();
      showToast(`Prompt compressed successfully! Saved ${result.tokens_saved} tokens (${result.compression_ratio}%).`);
    } catch (error) {
      console.error('Error executing prompt compression:', error);
      showToast(
        error.response?.data?.detail || 'Failed to connect to backend API at localhost:8000.',
        'error'
      );
    } finally {
      setIsCompressing(false);
    }
  };

  const handleReset = async () => {
    setIsResetting(true);
    try {
      await resetStats();
      setCompressionResult(null);
      await fetchSessionStats();
      showToast('Session statistics reset successfully.');
    } catch (error) {
      console.error('Error resetting stats:', error);
      showToast('Failed to reset session stats.', 'error');
    } finally {
      setIsResetting(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-zinc-950 text-zinc-100 font-sans relative">
      {/* Toast Alert Notification */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 animate-bounce-short">
          <div className={`flex items-center gap-3 px-4 py-3 rounded-xl border text-xs font-semibold shadow-2xl backdrop-blur-xl ${
            toastMessage.type === 'error'
              ? 'bg-rose-950/90 text-rose-300 border-rose-500/40'
              : 'bg-emerald-950/90 text-emerald-300 border-emerald-500/40'
          }`}>
            {toastMessage.type === 'error' ? (
              <AlertTriangle className="w-4 h-4 text-rose-400" />
            ) : (
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            )}
            <span>{toastMessage.message}</span>
          </div>
        </div>
      )}

      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} isBackendConnected={isBackendConnected} />

      <div className="flex-1 flex flex-col min-w-0">
        <Header onResetStats={handleReset} isResetting={isResetting} />

        <main className="flex-1 p-8 max-w-7xl w-full mx-auto space-y-8">
          {/* Top KPI Metrics Overview */}
          <StatsOverview stats={stats} />

          {/* Tab 1: Prompt Optimizer Workbench & Demo Selector */}
          {activeTab === 'optimizer' && (
            <div className="space-y-8">
              {/* Input Mode Selector Bar */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 bg-zinc-900/80 p-1 rounded-xl border border-white/10">
                  <button
                    onClick={() => setInputMode('demo')}
                    className={`flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-lg transition-all ${
                      inputMode === 'demo'
                        ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                        : 'text-zinc-400 hover:text-zinc-200'
                    }`}
                  >
                    <Sliders className="w-3.5 h-3.5" /> Built-in Scenarios (25–30 Turns)
                  </button>
                  <button
                    onClick={() => setInputMode('manual')}
                    className={`flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-lg transition-all ${
                      inputMode === 'manual'
                        ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                        : 'text-zinc-400 hover:text-zinc-200'
                    }`}
                  >
                    <Code2 className="w-3.5 h-3.5" /> Custom JSON / Input Prompt
                  </button>
                </div>
              </div>

              {inputMode === 'demo' ? (
                <DemoModeSelector
                  selectedPresetId={selectedPresetId}
                  onSelectPreset={handleSelectPreset}
                  topK={topK}
                  onTopKChange={setTopK}
                  onRunCompression={() => handleRunCompression()}
                  isCompressing={isCompressing}
                />
              ) : (
                <CustomInputForm
                  customQuery={customQuery}
                  onQueryChange={setCustomQuery}
                  rawHistoryJson={rawHistoryJson}
                  onRawHistoryChange={setRawHistoryJson}
                  onExecuteCompression={(parsedHistory, query) => handleRunCompression(parsedHistory, query)}
                  isCompressing={isCompressing}
                />
              )}

              {/* Compression Visualizer Component */}
              <CompressionVisualizer
                compressionResult={compressionResult}
                rawHistory={activeHistory}
                currentMessage={customQuery}
              />
            </div>
          )}

          {/* Tab 2: Live Analytics Charts */}
          {activeTab === 'analytics' && <AnalyticsCharts stats={stats} />}

          {/* Tab 3: Demo Mode Tab */}
          {activeTab === 'demo' && (
            <DemoModeSelector
              selectedPresetId={selectedPresetId}
              onSelectPreset={(id) => {
                handleSelectPreset(id);
                setActiveTab('optimizer');
              }}
              topK={topK}
              onTopKChange={setTopK}
              onRunCompression={() => {
                setActiveTab('optimizer');
                handleRunCompression();
              }}
              isCompressing={isCompressing}
            />
          )}

          {/* Tab 4: API Settings */}
          {activeTab === 'settings' && (
            <Card title="Middleware System Configuration" subtitle="Active settings & Gemini API status">
              <div className="space-y-4 py-2">
                <div className="p-4 rounded-xl bg-zinc-950/80 border border-zinc-800 flex items-center justify-between">
                  <div>
                    <h5 className="text-xs font-bold text-zinc-200">Backend API Base URL</h5>
                    <p className="text-xs text-zinc-500">FastAPI backend listener endpoint</p>
                  </div>
                  <code className="text-xs text-emerald-400 bg-zinc-900 px-3 py-1 rounded border border-zinc-800 font-mono">
                    http://localhost:8000/api/v1
                  </code>
                </div>

                <div className="p-4 rounded-xl bg-zinc-950/80 border border-zinc-800 flex items-center justify-between">
                  <div>
                    <h5 className="text-xs font-bold text-zinc-200">Embedding Model</h5>
                    <p className="text-xs text-zinc-500">Google Gemini Vector Embeddings</p>
                  </div>
                  <code className="text-xs text-violet-400 bg-zinc-900 px-3 py-1 rounded border border-zinc-800 font-mono">
                    text-embedding-004 (768 dimensions)
                  </code>
                </div>

                <div className="p-4 rounded-xl bg-zinc-950/80 border border-zinc-800 flex items-center justify-between">
                  <div>
                    <h5 className="text-xs font-bold text-zinc-200">Summarizer Model</h5>
                    <p className="text-xs text-zinc-500">Context Compressor LLM</p>
                  </div>
                  <code className="text-xs text-cyan-400 bg-zinc-900 px-3 py-1 rounded border border-zinc-800 font-mono">
                    gemini-1.5-flash
                  </code>
                </div>
              </div>
            </Card>
          )}
        </main>
      </div>
    </div>
  );
}
