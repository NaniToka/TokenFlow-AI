"""
RAG Hybrid Context Retriever.

Indexes text chunks in-memory, scores them against user queries using
hybrid BM25 and dense embeddings, and returns top-K context spans.
"""

from typing import Any

from app.services.llm.client import LLMClientManager
from app.services.rag.chunker import SemanticChunker, TextChunk
from app.services.ranking.engine import BM25Scorer, cosine_similarity


class ContextRetriever:
    """
    RAG retriever for long-form context documents and conversation transcripts.
    Supports in-memory indexing, semantic chunking, and dual-scoring retrieval.
    """

    def __init__(self, llm_client: LLMClientManager | None = None, chunk_size: int = 400, chunk_overlap: int = 80):
        self.chunker = SemanticChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self.llm_client = llm_client
        self.bm25 = BM25Scorer()
        self._chunks: list[TextChunk] = []
        self._embeddings: list[list[float]] = []

    @property
    def total_chunks(self) -> int:
        return len(self._chunks)

    def index_document_with_chunks(
        self,
        text: str,
        metadata: dict[str, Any] | None = None,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ) -> list[TextChunk]:
        """Chunks and indexes a document with optional custom chunker sizes, returning created chunks."""
        chunker = (
            SemanticChunker(
                chunk_size=chunk_size or self.chunker.chunk_size,
                chunk_overlap=chunk_overlap if chunk_overlap is not None else self.chunker.chunk_overlap,
            )
            if (chunk_size is not None or chunk_overlap is not None)
            else self.chunker
        )
        raw_chunks = chunker.split_text(text, metadata)
        base_id = len(self._chunks)
        new_chunks = [
            TextChunk(
                chunk_id=base_id + i,
                text=c.text,
                token_count=c.token_count,
                start_char=c.start_char,
                end_char=c.end_char,
                metadata=c.metadata,
            )
            for i, c in enumerate(raw_chunks)
        ]
        self._chunks.extend(new_chunks)

        if self.llm_client and self.llm_client.is_available:
            texts = [c.text for c in new_chunks]
            batch_vecs = self.llm_client.get_batch_embeddings(texts)
            self._embeddings.extend(batch_vecs)
        else:
            self._embeddings.extend([[] for _ in new_chunks])

        return new_chunks

    def index_document(self, text: str, metadata: dict[str, Any] | None = None) -> int:
        """Chunks and indexes a document for retrieval. Returns total indexed chunks."""
        new_chunks = self.index_document_with_chunks(text, metadata)
        return len(new_chunks)

    def retrieve(self, query: str, top_k: int = 3, alpha: float = 0.5) -> list[dict[str, Any]]:
        """
        Retrieves the top-K relevant chunks for a given query.
        Blends BM25 lexical match and dense semantic similarity.
        """
        if not self._chunks:
            return []

        doc_texts = [c.text for c in self._chunks]
        bm25_scores = self.bm25.score(query, doc_texts)

        query_vec = self.llm_client.get_embedding(query) if self.llm_client and self.llm_client.is_available else []

        results = []
        for i, chunk in enumerate(self._chunks):
            chunk_vec = self._embeddings[i] if i < len(self._embeddings) else []
            dense_sim = cosine_similarity(query_vec, chunk_vec) if query_vec and chunk_vec else 0.0

            # If offline (no dense embeddings), rely on BM25 score cleanly
            if not query_vec:
                hybrid = bm25_scores[i]
            else:
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

        results.sort(key=lambda x: float(str(x["hybrid_score"])), reverse=True)
        return results[:top_k]

    def clear(self) -> None:
        """Clears indexed documents."""
        self._chunks.clear()
        self._embeddings.clear()
