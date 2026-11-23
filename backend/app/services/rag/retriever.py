"""
RAG Hybrid Context Retriever.

Indexes text chunks in-memory, scores them against user queries using
hybrid BM25 and dense embeddings, and returns top-K context spans.
"""

from typing import List, Dict, Any
from app.services.rag.chunker import SemanticChunker, TextChunk
from app.services.ranking.engine import BM25Scorer, cosine_similarity
from app.services.llm.client import LLMClientManager


class ContextRetriever:
    """
    RAG retriever for long-form context documents and conversation transcripts.
    Supports in-memory indexing, semantic chunking, and dual-scoring retrieval.
    """

    def __init__(self, llm_client: LLMClientManager = None, chunk_size: int = 400, chunk_overlap: int = 80):
        self.chunker = SemanticChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self.llm_client = llm_client
        self.bm25 = BM25Scorer()
        self._chunks: List[TextChunk] = []
        self._embeddings: List[List[float]] = []

    def index_document(self, text: str, metadata: Dict[str, Any] = None) -> int:
        """Chunks and indexes a document for retrieval. Returns total indexed chunks."""
        new_chunks = self.chunker.split_text(text, metadata)
        start_idx = len(self._chunks)
        self._chunks.extend(new_chunks)

        if self.llm_client and self.llm_client.is_available:
            texts = [c.text for c in new_chunks]
            batch_vecs = self.llm_client.get_batch_embeddings(texts)
            self._embeddings.extend(batch_vecs)
        else:
            self._embeddings.extend([[] for _ in new_chunks])

        return len(new_chunks)

    def retrieve(self, query: str, top_k: int = 3, alpha: float = 0.5) -> List[Dict[str, Any]]:
        """
        Retrieves the top-K relevant chunks for a given query.
        Blends BM25 lexical match and dense semantic similarity.
        """
        if not self._chunks:
            return []

        doc_texts = [c.text for c in self._chunks]
        bm25_scores = self.bm25.score(query, doc_texts)

        # Dense similarity
        query_vec = self.llm_client.get_embedding(query) if self.llm_client and self.llm_client.is_available else []
        
        results = []
        for i, chunk in enumerate(self._chunks):
            chunk_vec = self._embeddings[i] if i < len(self._embeddings) else []
            dense_sim = cosine_similarity(query_vec, chunk_vec) if query_vec and chunk_vec else 0.0

            # Hybrid score
            hybrid = (alpha * dense_sim) + ((1.0 - alpha) * bm25_scores[i])
            results.append({
                "chunk_id": chunk.chunk_id,
                "text": chunk.text,
                "token_count": chunk.token_count,
                "bm25_score": round(bm25_scores[i], 4),
                "dense_score": round(dense_sim, 4),
                "hybrid_score": round(hybrid, 4),
                "metadata": chunk.metadata,
            })

        results.sort(key=lambda x: x["hybrid_score"], reverse=True)
        return results[:top_k]

    def clear(self):
        """Clears indexed documents."""
        self._chunks.clear()
        self._embeddings.clear()
