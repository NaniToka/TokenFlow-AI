import React, { useState } from 'react';
import { BookOpen, Search, Trash2, Layers, Sparkles, Upload, Quote } from 'lucide-react';
import Card from '../common/Card';
import ProgressRing from '../common/ProgressRing';
import { indexRagDocument, queryRagStore, clearRagStore, uploadRagFile } from '../../services/api';

const SAMPLE_DOC = `TokenFlow AI Architecture & Engineering Manual

1. Hybrid Ranking Engine & RRF Fusion
TokenFlow AI solves quadratic context bloat in multi-turn dialogues by blending Okapi BM25 sparse lexical matching with Gemini text-embedding-004 768-dimensional semantic vectors via Reciprocal Rank Fusion (RRF) and MMR diversity selection.

2. Conversational Drift Detection
Windowed Jaccard coherence identifies off-topic conversational tangents and applies a configurable drift penalty so noisy turns are evicted to hierarchical map-reduce summarization first.

3. Resilient Token Accounting
When running inside air-gapped VPCs or CI containers without blob download access, TokenFlow falls back to an offline regex subword tokenizer calibrated to BPE cl100k_base distributions.

4. Zero-Trust Privacy & Prompt Firewall
Zero user prompt text is ever persisted to databases. Inline PII redaction and INJ-001..005 injection scanning guard every request prior to upstream LLM forwarding.`;

export default function RagWorkbench({ onToast }) {
  const [docText, setDocText] = useState(SAMPLE_DOC);
  const [chunkSize, setChunkSize] = useState(280);
  const [chunkOverlap, setChunkOverlap] = useState(60);
  const [chunks, setChunks] = useState([]);
  const [totalStore, setTotalStore] = useState(0);

  const [query, setQuery] = useState('How does TokenFlow handle air-gapped token counting and RRF ranking?');
  const [alpha, setAlpha] = useState(0.5);
  const [useHyde, setUseHyde] = useState(true);
  const [useReranker, setUseReranker] = useState(true);
  const [queryMeta, setQueryMeta] = useState(null);
  const [results, setResults] = useState([]);
  const [isBusy, setIsBusy] = useState(false);

  const handleIndex = async () => {
    if (!docText.trim()) return;
    setIsBusy(true);
    try {
      const res = await indexRagDocument({
        text: docText,
        chunk_size: Number(chunkSize),
        chunk_overlap: Number(chunkOverlap),
        source_name: 'engineering_manual.md',
      });
      setChunks(res.chunks || []);
      setTotalStore(res.total_store_chunks || 0);
      onToast?.(`Indexed ${res.chunks_indexed} semantic chunks into RAG store.`);
    } catch {
      onToast?.('Failed to index document into RAG engine.', 'error');
    } finally {
      setIsBusy(false);
    }
  };

  const handleFileUpload = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = async () => {
      setIsBusy(true);
      try {
        const textContent = String(reader.result || '');
        const res = await uploadRagFile({
          filename: file.name,
          content: textContent,
          is_base64: false,
          chunk_size: Number(chunkSize),
          chunk_overlap: Number(chunkOverlap),
        });
        setDocText(textContent.slice(0, 20000));
        setChunks(res.chunks || []);
        setTotalStore(res.total_store_chunks || 0);
        onToast?.(`Uploaded & indexed "${file.name}" (${res.chunks_indexed} chunks).`);
      } catch (err) {
        onToast?.(err.response?.data?.detail || `Failed to ingest "${file.name}".`, 'error');
      } finally {
        setIsBusy(false);
        e.target.value = '';
      }
    };
    reader.readAsText(file);
  };

  const handleQuery = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    setIsBusy(true);
    try {
      const res = await queryRagStore({
        query,
        top_k: 4,
        alpha: Number(alpha),
        use_hyde: useHyde,
        use_reranker: useReranker,
      });
      setResults(res.results || []);
      setQueryMeta({
        expanded_query: res.expanded_query,
        added_terms: res.added_terms || [],
        citations: res.citations || {},
      });
      setTotalStore(res.total_indexed || 0);
    } catch {
      onToast?.('RAG query failed.', 'error');
    } finally {
      setIsBusy(false);
    }
  };

  const handleClear = async () => {
    await clearRagStore();
    setChunks([]);
    setResults([]);
    setQueryMeta(null);
    setTotalStore(0);
    onToast?.('RAG store cleared.');
  };

  return (
    <div className="space-y-6">
      <Card
        title="Semantic Document Chunker, Uploader & HyDE RAG Lab"
        subtitle="Ingest .md/.py/.txt/.json/.csv/.log specs, tune overlap windows, expand queries with HyDE, and audit [Chunk #i] grounding citations"
        action={
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-mono px-2.5 py-1 rounded-lg tf-subsurface tf-text-primary">
              Indexed: <strong className="text-emerald-500">{totalStore} chunks</strong>
            </span>
            <button
              type="button"
              onClick={handleClear}
              className="tf-btn-target flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-rose-500/10 text-rose-500 border border-rose-500/30 text-xs font-semibold cursor-pointer"
            >
              <Trash2 className="w-3.5 h-3.5" aria-hidden="true" /> Clear Store
            </button>
          </div>
        }
      >
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {/* Left: Document Upload, Chunker Parameters & Editor */}
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3 p-3 rounded-xl tf-subsurface">
              <label className="block text-xs tf-text-secondary">
                <span className="font-bold block mb-1">
                  Chunk Size: <strong className="font-mono text-emerald-500">{chunkSize} chars</strong>
                </span>
                <input
                  type="range"
                  min="150"
                  max="1000"
                  step="50"
                  value={chunkSize}
                  onChange={(e) => setChunkSize(Number(e.target.value))}
                  style={{ '--attr-min': 150, '--attr-max': 1000, '--control-value': chunkSize }}
                  className="tf-slider"
                />
              </label>

              <label className="block text-xs tf-text-secondary">
                <span className="font-bold block mb-1">
                  Overlap: <strong className="font-mono text-cyan-500">{chunkOverlap} chars</strong>
                </span>
                <input
                  type="range"
                  min="0"
                  max="200"
                  step="20"
                  value={chunkOverlap}
                  onChange={(e) => setChunkOverlap(Number(e.target.value))}
                  style={{ '--attr-min': 0, '--attr-max': 200, '--control-value': chunkOverlap }}
                  className="tf-slider"
                />
              </label>
            </div>

            {/* File Ingestion Control */}
            <div className="flex flex-wrap items-center justify-between gap-2 p-2.5 rounded-xl tf-subsurface">
              <span className="text-xs font-semibold tf-text-secondary">Ingest Local File (.md, .py, .txt, .json, .csv, .log):</span>
              <label className="tf-btn-target inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyan-500/15 text-cyan-500 border border-cyan-500/35 text-xs font-bold cursor-pointer">
                <Upload className="w-3.5 h-3.5" aria-hidden="true" />
                <span>Upload &amp; Index File</span>
                <input
                  type="file"
                  accept=".txt,.md,.py,.json,.csv,.log,.yaml,.yml"
                  onChange={handleFileUpload}
                  className="sr-only"
                />
              </label>
            </div>

            <label htmlFor="rag-doc-input" className="block text-xs font-bold uppercase tracking-wider tf-text-secondary">
              Source Document Content
            </label>
            <textarea
              id="rag-doc-input"
              rows={9}
              value={docText}
              onChange={(e) => setDocText(e.target.value)}
              className="tf-input w-full p-3 text-xs font-mono resize-y"
            />

            <button
              type="button"
              onClick={handleIndex}
              disabled={isBusy}
              className="tf-btn-target w-full flex items-center justify-center gap-2 py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-cyan-500 text-zinc-950 font-bold text-xs cursor-pointer disabled:opacity-50"
            >
              <Layers className="w-4 h-4" aria-hidden="true" />
              <span>Chunk &amp; Index Document</span>
            </button>
          </div>

          {/* Right: HyDE + Cross-Encoder Retrieval & Citation Grounding */}
          <div className="space-y-4">
            <search>
              <form onSubmit={handleQuery} className="p-3.5 rounded-xl tf-subsurface space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase tracking-wider tf-text-secondary flex items-center gap-1.5">
                    <Search className="w-3.5 h-3.5 text-emerald-500" aria-hidden="true" /> Hybrid Retrieval Query
                  </span>
                  <span className="text-[11px] font-mono tf-text-muted">Dense α={alpha.toFixed(2)}</span>
                </div>

                <div className="flex gap-2">
                  <input
                    type="search"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && e.nativeEvent.isComposing) e.preventDefault();
                    }}
                    aria-label="RAG retrieval query"
                    className="tf-input flex-1 px-3 py-2 text-xs"
                  />
                  <button
                    type="submit"
                    disabled={isBusy || totalStore === 0}
                    className="tf-btn-target px-4 py-2 rounded-xl bg-emerald-500 text-zinc-950 font-bold text-xs cursor-pointer disabled:opacity-40"
                  >
                    Retrieve
                  </button>
                </div>

                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={alpha}
                  onChange={(e) => setAlpha(parseFloat(e.target.value))}
                  aria-label="Hybrid dense vs BM25 weight"
                  style={{ '--attr-min': 0, '--attr-max': 1, '--control-value': alpha }}
                  className="tf-slider"
                />

                <div className="flex flex-wrap items-center gap-4 pt-1">
                  <label className="flex items-center gap-2 text-xs font-medium tf-text-primary cursor-pointer">
                    <input
                      type="checkbox"
                      switch=""
                      checked={useHyde}
                      onChange={(e) => setUseHyde(e.target.checked)}
                      className="tf-switch"
                    />
                    <span>HyDE Query Expansion</span>
                  </label>
                  <label className="flex items-center gap-2 text-xs font-medium tf-text-primary cursor-pointer">
                    <input
                      type="checkbox"
                      switch=""
                      checked={useReranker}
                      onChange={(e) => setUseReranker(e.target.checked)}
                      className="tf-switch"
                    />
                    <span>N-gram Cross-Reranker</span>
                  </label>
                </div>
              </form>
            </search>

            {/* HyDE Expansion Telemetry */}
            {queryMeta?.added_terms?.length > 0 && (
              <div className="p-3 rounded-xl tf-subsurface space-y-1.5 text-xs">
                <span className="font-bold text-[10px] uppercase tracking-wider text-cyan-500">
                  HyDE Expanded Synonyms Injected:
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {queryMeta.added_terms.map((term) => (
                    <span key={term} className="px-2 py-0.5 rounded bg-cyan-500/15 text-cyan-500 font-mono text-[10px] font-semibold">
                      +{term}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Citation Attributed Grounding Summary */}
            {queryMeta?.citations?.citations?.length > 0 && (
              <div className="p-3.5 rounded-xl bg-violet-500/10 border border-violet-500/30 flex items-center justify-between gap-4">
                <div className="space-y-1 min-w-0">
                  <h3 className="text-xs font-extrabold uppercase tracking-wider text-violet-400 flex items-center gap-1.5">
                    <Quote className="w-3.5 h-3.5" aria-hidden="true" /> Grounded Citation Summary
                  </h3>
                  <p className="text-xs font-mono tf-text-primary leading-relaxed line-clamp-3">
                    {queryMeta.citations.attributed_summary}
                  </p>
                </div>
                <ProgressRing
                  value={Math.round((queryMeta.citations.overall_confidence || 0) * 100)}
                  label="Citation grounding confidence"
                  displayValue={`${Math.round((queryMeta.citations.overall_confidence || 0) * 100)}%`}
                  subLabel="Grounded"
                  size={70}
                  thickness={6}
                  color="var(--accent-tertiary)"
                />
              </div>
            )}

            {/* Retrieval Hits */}
            {results.length > 0 && (
              <div className="space-y-2">
                <h3 className="text-xs font-bold uppercase tracking-wider text-emerald-500 flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5" aria-hidden="true" /> Top-K Retrieved &amp; Reranked Chunks
                </h3>
                {results.map((r) => (
                  <div key={r.chunk_id} className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-xs space-y-1.5">
                    <div className="flex flex-wrap items-center justify-between gap-2 font-mono text-[10px]">
                      <span className="font-bold text-emerald-500">
                        Chunk #{r.chunk_id} ({r.token_count} tok)
                      </span>
                      <span className="tf-text-secondary">
                        Hybrid: <strong>{r.hybrid_score}</strong> | BM25: {r.bm25_score} | Dense: {r.dense_score}
                        {r.rerank_score !== undefined ? ` | Rerank: ${r.rerank_score}` : ''}
                      </span>
                    </div>
                    <p className="tf-text-primary font-mono leading-relaxed">{r.text}</p>
                  </div>
                ))}
              </div>
            )}

            {/* Indexed Chunks List */}
            {chunks.length > 0 && (
              <div className="space-y-2">
                <h3 className="text-xs font-bold uppercase tracking-wider tf-text-secondary flex items-center gap-1.5">
                  <BookOpen className="w-3.5 h-3.5" aria-hidden="true" /> Semantic Chunk Boundaries ({chunks.length})
                </h3>
                <div className="max-h-52 overflow-y-auto tf-scroller space-y-2 pr-1">
                  {chunks.map((c) => (
                    <div key={c.chunk_id} className="p-2.5 rounded-lg tf-subsurface text-[11px] font-mono space-y-1">
                      <div className="flex justify-between tf-text-muted">
                        <span>Chunk #{c.chunk_id} ({c.metadata?.source || 'doc'})</span>
                        <span>chars [{c.start_char}..{c.end_char}] • ~{c.token_count} tok</span>
                      </div>
                      <p className="tf-text-secondary line-clamp-2">{c.text}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </Card>
    </div>
  );
}
