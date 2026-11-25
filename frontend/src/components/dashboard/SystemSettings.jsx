import React, { useEffect, useState } from 'react';
import { ShieldCheck, Sun, Moon, Monitor, Terminal, CheckCircle2, AlertTriangle, Copy, Check } from 'lucide-react';
import Card from '../common/Card';
import { getHealth, sanitizeText } from '../../services/api';

export default function SystemSettings({
  themePreference,
  systemTheme,
  onSetTheme,
  targetModel,
  compressionMode,
  topK,
}) {
  const [health, setHealth] = useState(null);
  const [rawSample, setRawSample] = useState(
    'Debug DB with key sk-9876543210abcdef9876543210abcdef, email sre@company.com, IP 10.0.4.22 <script>alert(1)</script>'
  );
  const [scanResult, setScanResult] = useState(null);
  const [copiedCurl, setCopiedCurl] = useState(false);

  useEffect(() => {
    getHealth().then(setHealth).catch(() => {});
  }, []);

  const handleRunSanitizer = async () => {
    try {
      const res = await sanitizeText(rawSample, true);
      setScanResult(res);
    } catch {
      // ignore
    }
  };

  const curlCommand = `curl -X POST http://localhost:8000/api/v1/compress \\
  -H "Content-Type: application/json" \\
  -d '{
    "history": [{"role": "user", "content": "Deploying Postgres with PgBouncer."}],
    "current_message": "How do I configure transaction pooling?",
    "top_k": ${topK},
    "target_model": "${targetModel}",
    "compression_mode": "${compressionMode}",
    "sanitize_pii": true
  }'`;

  const handleCopyCurl = () => {
    navigator.clipboard.writeText(curlCommand);
    setCopiedCurl(true);
    setTimeout(() => setCopiedCurl(false), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Tri-state Theme Preference Surface (modern-web-guidance compliant) */}
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

      {/* Live PII Redaction & XSS Scanner Tester */}
      <Card
        title="PII Redaction & Prompt Sanitization Guardrail"
        subtitle="Test zero-trust secret masking (API keys, JWTs, Emails, IPv4, SSNs, XSS payloads)"
        action={
          <button
            type="button"
            onClick={handleRunSanitizer}
            className="tf-btn-target flex items-center gap-1.5 px-4 py-1.5 rounded-xl bg-amber-500/15 text-amber-500 border border-amber-500/35 text-xs font-bold cursor-pointer"
          >
            <ShieldCheck className="w-4 h-4" aria-hidden="true" />
            <span>Scan &amp; Redact Text</span>
          </button>
        }
      >
        <div className="space-y-3">
          <textarea
            rows={3}
            value={rawSample}
            onChange={(e) => setRawSample(e.target.value)}
            aria-label="Test text for PII and XSS sanitization"
            className="tf-input w-full p-3 text-xs font-mono resize-y"
          />

          {scanResult && (
            <div className="p-3.5 rounded-xl tf-subsurface space-y-2 text-xs">
              <div className="flex flex-wrap items-center gap-2 font-mono">
                <span className="px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-500 font-bold">
                  {scanResult.redactions_count} Secrets Masked
                </span>
                <span className="px-2 py-0.5 rounded bg-rose-500/15 text-rose-500 font-bold">
                  {scanResult.xss_stripped} XSS Vectors Stripped
                </span>
                {scanResult.redacted_types.map((t) => (
                  <span key={t} className="px-2 py-0.5 rounded tf-card tf-text-secondary">
                    {t}
                  </span>
                ))}
              </div>
              <pre className="p-2.5 rounded-lg tf-card font-mono tf-text-primary whitespace-pre-wrap">
                {scanResult.sanitized_text}
              </pre>
            </div>
          )}
        </div>
      </Card>

      {/* Feature Flags & Live cURL Generator */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
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

        <Card
          title="Live API Integration Snippet"
          subtitle="Copy ready-to-run cURL reflecting your current model and strategy settings"
          action={
            <button
              type="button"
              onClick={handleCopyCurl}
              className="tf-btn-target flex items-center gap-1.5 px-3 py-1.5 rounded-xl tf-subsurface text-xs font-semibold tf-text-primary cursor-pointer"
            >
              {copiedCurl ? <Check className="w-3.5 h-3.5 text-emerald-500" aria-hidden="true" /> : <Copy className="w-3.5 h-3.5" aria-hidden="true" />}
              <span>{copiedCurl ? 'Copied' : 'Copy cURL'}</span>
            </button>
          }
        >
          <div className="p-3 rounded-xl tf-subsurface overflow-x-auto tf-scroller">
            <pre className="text-[11px] font-mono tf-text-primary whitespace-pre leading-relaxed">
              <Terminal className="w-3.5 h-3.5 inline text-emerald-500 mr-1.5" aria-hidden="true" />
              {curlCommand}
            </pre>
          </div>
        </Card>
      </div>
    </div>
  );
}
