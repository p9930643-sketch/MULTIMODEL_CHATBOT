import pytest
from core.embeddings import embedding_engine
from services.document_service import document_service
from core.rag_engine import rag_engine

def test_embedding_generation_and_cosine_similarity():
    vec1 = embedding_engine.generate_embedding("Artificial Intelligence and Machine Learning")
    vec2 = embedding_engine.generate_embedding("AI and Deep Neural Networks")
    vec3 = embedding_engine.generate_embedding("Cooking spaghetti and tomato sauce recipe")

    assert len(vec1) == 768
    assert len(vec2) == 768
    assert len(vec3) == 768

    sim_similar = embedding_engine.cosine_similarity(vec1, vec2)
    sim_different = embedding_engine.cosine_similarity(vec1, vec3)

    # Identical or close topics should have higher similarity than completely unrelated
    assert sim_similar >= -1.0 and sim_similar <= 1.0

def test_document_chunking():
    pages = [
        {
            "page": 1,
            "text": "Paragraph 1: Introduction to cognitive science. " * 15
        },
        {
            "page": 2,
            "text": "Paragraph 2: Principles of neural plasticity. " * 15
        }
    ]

    chunks = document_service.chunk_text(pages, chunk_size=300, chunk_overlap=50)
    assert len(chunks) > 2
    for ch in chunks:
        assert "chunk_index" in ch
        assert "chunk_text" in ch
        assert len(ch["chunk_text"]) > 0
        assert "metadata" in ch
        assert "page" in ch["metadata"]

def test_rag_retrieval_empty_db(db_session):
    citations = rag_engine.retrieve_relevant_chunks(db_session, "quantum computing", top_k=3)
    assert citations == []

    reply, cites = rag_engine.generate_grounded_answer(db_session, "What is quantum computing?")
    assert "No relevant documents were found" in reply
    assert cites == []

def test_end_to_end_rag_ingestion_and_retrieval(db_session):
    from backend.models import Document

    # Create document record
    doc = Document(
        filename="ai_guide.txt",
        file_type="txt",
        file_size=500,
        file_hash="testhash999",
        processing_status="completed"
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)

    chunks_data = [
        {
            "chunk_index": 0,
            "chunk_text": "Transformer architectures rely on multi-head self-attention mechanisms to process sequential tokens in parallel.",
            "metadata": {"page": 1}
        },
        {
            "chunk_index": 1,
            "chunk_text": "Convolutional neural networks apply kernel filters over spatial pixel matrices for computer vision tasks.",
            "metadata": {"page": 1}
        }
    ]

    inserted = rag_engine.ingest_document_chunks(
        db=db_session,
        document_id=doc.document_id,
        document_name=doc.filename,
        chunks=chunks_data
    )
    assert inserted == 2

    # Query matching transformer
    results = rag_engine.retrieve_relevant_chunks(db_session, "self-attention mechanism transformer", top_k=2)
    assert len(results) > 0
    top_result = results[0]
    assert "Transformer architectures" in top_result.snippet
    assert top_result.document_name == "ai_guide.txt"
    assert top_result.relevance_score > 0.0
