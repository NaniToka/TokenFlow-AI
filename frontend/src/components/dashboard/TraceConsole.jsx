import React, { useCallback, useEffect, useState } from 'react';
import { Activity, RefreshCw, Trash2, Search, ZapOff, ShieldCheck, RotateCcw } from 'lucide-react';
import Card from '../common/Card';
import {
  getAuditLogs,
  clearAuditLogs,
  getCircuitBreaker,
  resetCircuitBreaker,
} from '../../services/api';

export default function TraceConsole({ onToast }) {
  const [logs, setLogs] = useState([]);
  const [breaker, setBreaker] = useState({ state: 'CLOSED', failure_count: 0, failure_threshold: 3, total_trips: 0 });
  const [filterText, setFilterText] = useState('');
  const [autoPoll, setAutoPoll] = useState(true);
  const [isLoading, setIsLoading] = useState(false);

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    try {
      const [logsRes, breakerRes] = await Promise.all([
        getAuditLogs(50),
        getCircuitBreaker(),
      ]);
      setLogs(logsRes.logs || []);
      setBreaker(breakerRes);
    } catch {
      // Ignore transient poll errors when offline
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    if (!autoPoll) return undefined;
    const id = setInterval(fetchData, 4000);
    return () => clearInterval(id);
  }, [fetchData, autoPoll]);

  const handleClearLogs = async () => {
    await clearAuditLogs();
    setLogs([]);
    onToast?.('Audit trace ring buffer cleared.');
  };

  const handleResetBreaker = async () => {
    const res = await resetCircuitBreaker();
    setBreaker(res.circuit_breaker);
    onToast?.('LLM circuit breaker reset to CLOSED state.');
  };

  const q = filterText.trim().toLowerCase();
  const filteredLogs = q
    ? logs.filter(
        (entry) =>
          String(entry.event || '').toLowerCase().includes(q) ||
          String(entry.correlation_id || '').toLowerCase().includes(q) ||
          String(entry.status_code || '').includes(q)
      )
    : logs;

  const isClosed = breaker.state === 'CLOSED';

  return (
    <div className="space-y-6">
      {/* Upstream LLM Circuit Breaker Card */}
      <Card
        title="Upstream LLM Fault-Tolerance & Circuit Breaker"
        subtitle="3-state CLOSED / OPEN / HALF_OPEN guard preventing cascading latency stalls during upstream provider outages"
        action={
          <button
            type="button"
            onClick={handleResetBreaker}
            className="tf-btn-target flex items-center gap-1.5 px-3 py-1.5 rounded-xl tf-subsurface text-xs font-semibold tf-text-primary hover:border-emerald-500/40 cursor-pointer"
          >
            <RotateCcw className="w-3.5 h-3.5 text-emerald-500" aria-hidden="true" />
            <span>Reset Breaker</span>
          </button>
        }
      >
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
          <div className="p-3.5 rounded-xl tf-subsurface flex items-center gap-3">
            {isClosed ? (
              <ShieldCheck className="w-6 h-6 text-emerald-500 shrink-0" aria-hidden="true" />
            ) : (
              <ZapOff className="w-6 h-6 text-rose-500 shrink-0" aria-hidden="true" />
            )}
            <div>
              <p className="text-[10px] font-bold uppercase tf-text-muted">State</p>
              <p className={`text-sm font-mono font-extrabold ${isClosed ? 'text-emerald-500' : 'text-rose-500'}`}>
                {breaker.state}
              </p>
            </div>
          </div>

          <div className="p-3.5 rounded-xl tf-subsurface">
            <p className="text-[10px] font-bold uppercase tf-text-muted">Consecutive Failures</p>
            <p className="text-sm font-mono font-extrabold tf-text-primary">
              {breaker.failure_count} / {breaker.failure_threshold}
            </p>
          </div>

          <div className="p-3.5 rounded-xl tf-subsurface">
            <p className="text-[10px] font-bold uppercase tf-text-muted">Lifetime Trips</p>
            <p className="text-sm font-mono font-extrabold tf-text-primary">{breaker.total_trips}</p>
          </div>

          <div className="p-3.5 rounded-xl tf-subsurface flex items-center justify-between">
            <span className="text-xs font-semibold tf-text-secondary">Auto-Poll (4s)</span>
            <input
              type="checkbox"
              switch=""
              aria-label="Enable auto polling trace console"
              checked={autoPoll}
              onChange={(e) => setAutoPoll(e.target.checked)}
              className="tf-switch"
            />
          </div>
        </div>
      </Card>

      {/* Audit Log Ring Buffer */}
      <Card
        title="Zero-PII Request Trace Audit Console"
        subtitle="Real-time bounded ring buffer of API telemetry, X-Request-ID correlation hashes, and end-to-end latencies (never stores prompts)"
        action={
          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={fetchData}
              className="tf-btn-target flex items-center gap-1.5 px-3 py-1.5 rounded-xl tf-subsurface text-xs font-semibold tf-text-primary cursor-pointer"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} aria-hidden="true" />
              <span>Refresh</span>
            </button>
            <button
              type="button"
              onClick={handleClearLogs}
              className="tf-btn-target flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-rose-500/10 text-rose-500 border border-rose-500/30 text-xs font-semibold cursor-pointer"
            >
              <Trash2 className="w-3.5 h-3.5" aria-hidden="true" />
              <span>Clear Buffer</span>
            </button>
          </div>
        }
      >
        <div className="space-y-4">
          <search className="block relative">
            <Search className="w-4 h-4 tf-text-muted absolute left-3 top-2.5" aria-hidden="true" />
            <input
              type="search"
              value={filterText}
              onChange={(e) => setFilterText(e.target.value)}
              aria-label="Filter telemetry logs by route, correlation ID, or status code"
              placeholder="Filter traces by route (/compress, /rag/query), status code, or X-Request-ID..."
              className="tf-input w-full pl-9 pr-3 py-2 text-xs font-mono"
            />
          </search>

          {filteredLogs.length === 0 ? (
            <div className="py-10 text-center space-y-2 tf-subsurface rounded-xl border border-dashed">
              <Activity className="w-6 h-6 tf-text-muted mx-auto" aria-hidden="true" />
              <p className="text-xs font-semibold tf-text-secondary">No trace records match current filter.</p>
            </div>
          ) : (
            <div className="tf-table-wrapper tf-scroller">
              <table className="tf-audit-table">
                <caption className="visually-hidden">Recent API telemetry trace log entries</caption>
                <thead>
                  <tr>
                    <th scope="col">Timestamp (UTC)</th>
                    <th scope="col">Event / Endpoint</th>
                    <th scope="col">Correlation ID</th>
                    <th scope="col">Status</th>
                    <th scope="col">Latency</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredLogs.map((entry, idx) => (
                    <tr key={`${entry.correlation_id}-${idx}`}>
                      <td data-label="Time" className="font-mono text-[11px] tf-text-muted">
                        {String(entry.timestamp || '').replace('T', ' ').slice(0, 19)}
                      </td>
                      <th scope="row" className="font-mono font-bold tf-text-primary">{entry.event}</th>
                      <td data-label="Correlation" className="font-mono text-[11px] text-cyan-500">
                        {entry.correlation_id}
                      </td>
                      <td data-label="Status">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                          entry.status_code < 400
                            ? 'bg-emerald-500/15 text-emerald-500'
                            : 'bg-rose-500/15 text-rose-500'
                        }`}>
                          {entry.status_code}
                        </span>
                      </td>
                      <td data-label="Latency" className="font-mono font-bold tf-text-secondary">
                        {entry.latency_ms} ms
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}
