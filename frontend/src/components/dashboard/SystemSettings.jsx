import React, { useEffect, useState } from 'react';
import { ShieldCheck, Sun, Moon, Monitor, Terminal, CheckCircle2, AlertTriangle, Copy, Check, Send } from 'lucide-react';
import Card from '../common/Card';
import { getHealth, sanitizeText, getSdkSnippets, compressOpenAIChat } from '../../services/api';

const SDK_LANGS = [
  { id: 'curl', label: 'cURL' },
  { id: 'python', label: 'Python httpx' },
  { id: 'typescript', label: 'TypeScript fetch' },
  { id: 'openai_adapter', label: 'OpenAI Drop-in' },
];

export default function SystemSettings({
  themePreference,
  systemTheme,
  onSetTheme,
  targetModel,
  compressionMode,
  topK,
  fusionMethod = 'rrf',
  sanitizePii = true,
}) {
  const [health, setHealth] = useState(null);
  const [rawSample, setRawSample] = useState(
    'Debug DB with key sk-9876543210abcdef9876543210abcdef, email sre@company.com, IP 10.0.4.22 <script>alert(1)</script>'
  );
  const [scanResult, setScanResult] = useState(null);

  const [sdkLang, setSdkLang] = useState('python');
  const [snippets, setSnippets] = useState(null);
  const [copiedCode, setCopiedCode] = useState(false);

  const [openAiRes, setOpenAiRes] = useState(null);
  const [isTestingOpenAi, setIsTestingOpenAi] = useState(false);

  useEffect(() => {
    getHealth().then(setHealth).catch(() => {});
  }, []);

  useEffect(() => {
    getSdkSnippets({
      target_model: targetModel,
      compression_mode: compressionMode,
      top_k: topK,
      fusion_method: fusionMethod,
      sanitize_pii: sanitizePii,
    })
      .then(setSnippets)
      .catch(() => {});
  }, [targetModel, compressionMode, topK, fusionMethod, sanitizePii]);

  const handleRunSanitizer = async () => {
    try {
      const res = await sanitizeText(rawSample, true);
      setScanResult(res);
    } catch {
      // ignore offline error
    }
  };

  const fallbackCurl = `curl -X POST http://localhost:8000/api/v1/compress \\
  -H "Content-Type: application/json" \\
  -d '{
    "history": [{"role": "user", "content": "Deploying Postgres with PgBouncer."}],
    "current_message": "How do I configure transaction pooling?",
    "top_k": ${topK},
    "target_model": "${targetModel}",
    "compression_mode": "${compressionMode}",
    "fusion_method": "${fusionMethod}",
    "sanitize_pii": ${sanitizePii}
  }'`;

  const activeSnippet = snippets?.[sdkLang] || fallbackCurl;

  const handleCopySnippet = () => {
    navigator.clipboard.writeText(activeSnippet);
    setCopiedCode(true);
    setTimeout(() => setCopiedCode(false), 2000);
  };

  const handleTestOpenAIAdapter = async () => {
    setIsTestingOpenAi(true);
    try {
      const res = await compressOpenAIChat({
        messages: [
          { role: 'system', content: 'You are a distributed systems staff engineer.' },
          { role: 'user', content: 'Our Kafka consumer group experiences rebalance storms during deploys.' },
          { role: 'assistant', content: 'Use cooperative-sticky assignor and static group membership.' },
          { role: 'user', content: 'By the way, what pizza topping do you prefer?' },
          { role: 'user', content: 'Which session.timeout.ms value stabilizes Kubernetes rolling restarts?' },
        ],
        top_k: topK,
        target_model: targetModel,
        compression_mode: compressionMode,
        sanitize_pii: sanitizePii,
      });
      setOpenAiRes(res);
    } catch {
      // ignore offline error
    } finally {
      setIsTestingOpenAi(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Tri-state Theme Preference Surface */}
      <Card
        title="Appearance & System Color Scheme"
        subtitle="Syncs natively with <meta name='color-scheme'> and CSS light-dark() across browser tabs"
      >
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {[
            {
              id: 'system',
              label: `System (Currently ${systemTheme})`,
              desc: 'Follow OS light/dark schedule automatically',
              icon: Monitor,
            },
            {
              id: 'light',
              label: 'Lab Light',
              desc: 'High-contrast daylight academic surfaces',
              icon: Sun,
            },
            {
              id: 'dark',
              label: 'Obsidian Dark',
              desc: 'Low-glare carbon engineering console',
              icon: Moon,
            },
          ].map((opt) => {
            const Icon = opt.icon;
            const active = themePreference === opt.id;
            return (
              <button
                key={opt.id}
                type="button"
                onClick={() => onSetTheme(opt.id)}
                aria-pressed={active}
                className={`p-4 rounded-xl border text-left transition-all cursor-pointer ${
                  active
                    ? 'bg-emerald-500/10 border-emerald-500/45 shadow-sm'
                    : 'tf-subsurface hover:border-emerald-500/30'
                }`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <Icon className={`w-4 h-4 ${active ? 'text-emerald-500' : 'tf-text-secondary'}`} aria-hidden="true" />
                  {active && <CheckCircle2 className="w-4 h-4 text-emerald-500" aria-hidden="true" />}
                </div>
                <p className="text-xs font-bold tf-text-primary">{opt.label}</p>
                <p className="text-[11px] tf-text-secondary mt-0.5">{opt.desc}</p>
              </button>
            );
          })}
        </div>
      </Card>

      {/* Multi-Language SDK Code Generator + OpenAI Adapter Tester */}
      <Card
        title="Multi-Language SDK Snippets & OpenAI Drop-In Proxy Tester"
        subtitle="Copy pre-configured integration code or test OpenAI-compatible `POST /api/v1/chat/compress` payloads live"
        action={
          <button
            type="button"
            onClick={handleCopySnippet}
            className="tf-btn-target flex items-center gap-1.5 px-3 py-1.5 rounded-xl tf-subsurface text-xs font-semibold tf-text-primary cursor-pointer"
          >
            {copiedCode ? <Check className="w-3.5 h-3.5 text-emerald-500" aria-hidden="true" /> : <Copy className="w-3.5 h-3.5" aria-hidden="true" />}
            <span>{copiedCode ? 'Copied Snippet' : 'Copy Code'}</span>
          </button>
        }
      >
        <div className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap gap-1.5 p-1 rounded-xl tf-subsurface">
              {SDK_LANGS.map((lang) => (
                <button
                  key={lang.id}
                  type="button"
                  onClick={() => setSdkLang(lang.id)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold cursor-pointer ${
                    sdkLang === lang.id
                      ? 'bg-emerald-500/20 text-emerald-500 border border-emerald-500/35'
                      : 'tf-text-secondary hover:opacity-85'
                  }`}
                >
                  {lang.label}
                </button>
              ))}
            </div>

            <button
              type="button"
              onClick={handleTestOpenAIAdapter}
              disabled={isTestingOpenAi}
              className="tf-btn-target flex items-center gap-1.5 px-4 py-1.5 rounded-xl bg-cyan-500/15 text-cyan-500 border border-cyan-500/35 text-xs font-bold cursor-pointer disabled:opacity-50"
            >
              <Send className="w-3.5 h-3.5" aria-hidden="true" />
              <span>{isTestingOpenAi ? 'Compressing...' : 'Test OpenAI Chat Adapter'}</span>
            </button>
          </div>

          <div className="p-3.5 rounded-xl tf-subsurface overflow-x-auto tf-scroller">
            <pre className="text-[11px] font-mono tf-text-primary whitespace-pre leading-relaxed">
              <Terminal className="w-3.5 h-3.5 inline text-emerald-500 mr-1.5" aria-hidden="true" />
              {activeSnippet}
            </pre>
          </div>

          {openAiRes && (
            <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 space-y-2 text-xs font-mono">
              <div className="flex flex-wrap items-center justify-between gap-2 text-emerald-500 font-bold">
                <span>OpenAI Adapter Output ({openAiRes.messages?.length || 0} compressed messages)</span>
                <span>Saved {openAiRes.tokens_saved} tokens ({openAiRes.compression_ratio}%)</span>
              </div>
              <pre className="p-2.5 rounded-lg tf-card tf-text-primary overflow-x-auto tf-scroller text-[11px]">
                {JSON.stringify(openAiRes.messages, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </Card>

      {/* Live PII Redaction & Runtime Feature Flags */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card
          title="Quick PII Redaction & Sanitizer"
          subtitle="Validate API key, JWT, email, and XSS sanitization rules"
          action={
            <button
              type="button"
              onClick={handleRunSanitizer}
              className="tf-btn-target flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-amber-500/15 text-amber-500 border border-amber-500/35 text-xs font-bold cursor-pointer"
            >
              <ShieldCheck className="w-3.5 h-3.5" aria-hidden="true" />
              <span>Redact</span>
            </button>
          }
        >
          <div className="space-y-3">
            <textarea
              rows={3}
              value={rawSample}
              onChange={(e) => setRawSample(e.target.value)}
              aria-label="Test text for PII sanitization"
              className="tf-input w-full p-3 text-xs font-mono resize-y"
            />
            {scanResult && (
              <pre className="p-2.5 rounded-lg tf-subsurface text-[11px] font-mono tf-text-primary whitespace-pre-wrap">
                {scanResult.sanitized_text}
              </pre>
            )}
          </div>
        </Card>

        <Card title="Active Runtime Feature Flags" subtitle={health ? `Version ${health.version} (${health.environment})` : 'Checking server...'}>
          <div className="space-y-2">
            {health?.features ? (
              Object.entries(health.features).map(([flag, enabled]) => (
                <div key={flag} className="p-2.5 rounded-xl tf-subsurface flex items-center justify-between text-xs">
                  <span className="font-mono font-semibold tf-text-primary">{flag}</span>
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                    enabled ? 'bg-emerald-500/15 text-emerald-500' : 'tf-card tf-text-muted'
                  }`}>
                    {enabled ? 'Enabled' : 'Disabled'}
                  </span>
                </div>
              ))
            ) : (
              <p className="text-xs tf-text-muted flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-500" aria-hidden="true" /> Loading runtime diagnostics...
              </p>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}
