import pytest
from app.services.rag.chunker import SemanticChunker, TextChunk
from app.services.rag.retriever import ContextRetriever


def test_semantic_chunker_basic():
    chunker = SemanticChunker(chunk_size=100, chunk_overlap=20)
    text = "Paragraph one with some interesting content.\n\nParagraph two with more details.\n\nParagraph three concluding thoughts."
    chunks = chunker.split_text(text)
    assert len(chunks) >= 2
    assert all(isinstance(c, TextChunk) for c in chunks)
    assert all(c.token_count > 0 for c in chunks)


def test_semantic_chunker_empty():
    chunker = SemanticChunker()
    assert chunker.split_text("") == []
    assert chunker.split_text("   ") == []


def test_context_retriever_indexing_and_search():
    retriever = ContextRetriever(chunk_size=200, chunk_overlap=30)
    doc = """
    PostgreSQL connection pooling is critical for performance.
    PgBouncer maintains a pool of database connections and multiplexes queries.
    Redis can also be used as a cache layer to bypass database queries entirely.
    """
    count = retriever.index_document(doc, metadata={"source": "db_guide"})
    assert count >= 1

    results = retriever.retrieve("How does PgBouncer pool connections?", top_k=2)
    assert len(results) >= 1
    assert "PgBouncer" in results[0]["text"]
    assert "hybrid_score" in results[0]
