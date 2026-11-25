import React, { useState } from 'react';
import { BookOpen, Search, Trash2, Layers, Sparkles } from 'lucide-react';
import Card from '../common/Card';
import { indexRagDocument, queryRagStore, clearRagStore } from '../../services/api';

const SAMPLE_DOC = `TokenFlow AI Architecture & Engineering Manual

1. Hybrid Ranking Engine
TokenFlow AI solves quadratic context bloat in multi-turn dialogues by blending Okapi BM25 sparse lexical matching with Gemini text-embedding-004 768-dimensional semantic vectors. Recency decay uses exp(-0.05 * distance) so immediate operational context remains prioritized.

2. Conversational Drift Detection
Windowed Jaccard coherence identifies off-topic conversational tangents (such as team lunch chatter or unrelated trivia) and applies a configurable drift penalty so noisy turns are evicted to background summarization first.

3. Resilient Token Accounting
When running inside air-gapped VPCs or CI containers without blob download access, TokenFlow falls back to an offline regex subword tokenizer calibrated to BPE cl100k_base distributions.

4. Stateless Privacy & PII Guard
Zero user prompt text is ever persisted to databases. Optional inline PII redaction masks OpenAI keys, Gemini keys, JWT tokens, email addresses, and IPv4 addresses prior to upstream LLM forwarding.`;

export default function RagWorkbench({ onToast }) {
  const [docText, setDocText] = useState(SAMPLE_DOC);
  const [chunkSize, setChunkSize] = useState(280);
  const [chunkOverlap, setChunkOverlap] = useState(60);
  const [chunks, setChunks] = useState([]);
  const [totalStore, setTotalStore] = useState(0);

  const [query, setQuery] = useState('How does TokenFlow handle air-gapped token counting?');
  const [alpha, setAlpha] = useState(0.5);
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

  const handleQuery = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    setIsBusy(true);
    try {
      const res = await queryRagStore({ query, top_k: 3, alpha: Number(alpha) });
      setResults(res.results || []);
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
    setTotalStore(0);
    onToast?.('RAG store cleared.');
  };

  return (
    <div className="space-y-6">
      <Card
        title="Semantic Document Chunker & In-Memory RAG Lab"
        subtitle="Split technical specifications along paragraph/sentence boundaries and test hybrid BM25 + dense vector retrieval"
        action={
          <div className="flex items-center gap-2">
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
          {/* Left: Document & Chunker Parameters */}
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3 p-3 rounded-xl tf-subsurface">
              <label className="block text-xs tf-text-secondary">
                <span className="font-bold block mb-1">Chunk Size: <strong className="font-mono text-emerald-500">{chunkSize} chars</strong></span>
                <input
                  type="range"
                  min="150"
                  max="1000"
                  step="50"
                  value={chunkSize}
                  onChange={(e) => setChunkSize(Number(e.target.value))}
                  className="w-full cursor-pointer"
                />
              </label>

              <label className="block text-xs tf-text-secondary">
                <span className="font-bold block mb-1">Overlap: <strong className="font-mono text-cyan-500">{chunkOverlap} chars</strong></span>
                <input
                  type="range"
                  min="0"
                  max="200"
                  step="20"
                  value={chunkOverlap}
                  onChange={(e) => setChunkOverlap(Number(e.target.value))}
                  className="w-full cursor-pointer"
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

          {/* Right: Generated Chunks & Live Retrieval */}
          <div className="space-y-4">
            <form onSubmit={handleQuery} className="p-3.5 rounded-xl tf-subsurface space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider tf-text-secondary flex items-center gap-1.5">
                  <Search className="w-3.5 h-3.5 text-emerald-500" aria-hidden="true" /> Hybrid Retrieval Query
                </span>
                <span className="text-[11px] font-mono tf-text-muted">α={alpha.toFixed(2)}</span>
              </div>

              <div className="flex gap-2">
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
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
                className="w-full cursor-pointer"
              />
            </form>

            {/* Retrieval Hits */}
            {results.length > 0 && (
              <div className="space-y-2">
                <h3 className="text-xs font-bold uppercase tracking-wider text-emerald-500 flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5" aria-hidden="true" /> Top-K Retrieved Chunks
                </h3>
                {results.map((r) => (
                  <div key={r.chunk_id} className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-xs space-y-1.5">
                    <div className="flex flex-wrap items-center justify-between gap-2 font-mono text-[10px]">
                      <span className="font-bold text-emerald-500">Chunk #{r.chunk_id} ({r.token_count} tok)</span>
                      <span className="tf-text-secondary">
                        Hybrid: <strong>{r.hybrid_score}</strong> | BM25: {r.bm25_score} | Dense: {r.dense_score}
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
                <div className="max-h-56 overflow-y-auto tf-scroller space-y-2 pr-1">
                  {chunks.map((c) => (
                    <div key={c.chunk_id} className="p-2.5 rounded-lg tf-subsurface text-[11px] font-mono space-y-1">
                      <div className="flex justify-between tf-text-muted">
                        <span>Chunk #{c.chunk_id}</span>
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
