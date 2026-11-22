import pytest
from datetime import datetime
from backend.models import Conversation, Message, Document, DocumentChunk, KnowledgeSource
from backend.database import init_engine, create_tables

def test_database_models_crud(db_session):
    # 1. Conversation CRUD
    conv = Conversation(title="DB Test Conversation")
    db_session.add(conv)
    db_session.commit()
    db_session.refresh(conv)

    assert conv.conversation_id is not None
    assert conv.title == "DB Test Conversation"

    # 2. Message CRUD
    msg = Message(
        conversation_id=conv.conversation_id,
        sender="user",
        message_content="Testing database persistence",
        modality="text",
        metadata_json={"test_key": "test_val"}
    )
    db_session.add(msg)
    db_session.commit()
    db_session.refresh(msg)

    assert msg.message_id is not None
    assert msg.conversation_id == conv.conversation_id
    assert msg.metadata_json == {"test_key": "test_val"}

    # 3. Document & Chunks CRUD
    doc = Document(
        filename="test_policy.pdf",
        file_type="pdf",
        file_size=1024,
        file_hash="dummyhash123456",
        processing_status="completed"
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)

    assert doc.document_id is not None

    chunk = DocumentChunk(
        document_id=doc.document_id,
        chunk_index=0,
        chunk_text="This is an internal test policy chunk.",
        embedding=[0.1] * 768,
        chunk_metadata={"page": 1}
    )
    db_session.add(chunk)

    source = KnowledgeSource(
        document_id=doc.document_id,
        source_name="Company Policy 2026",
        source_metadata={"section": "Compliance"}
    )
    db_session.add(source)
    db_session.commit()

    # Query verification
    queried_chunk = db_session.query(DocumentChunk).filter(DocumentChunk.document_id == doc.document_id).first()
    assert queried_chunk is not None
    assert queried_chunk.chunk_text == "This is an internal test policy chunk."
    assert len(queried_chunk.embedding) == 768

    queried_source = db_session.query(KnowledgeSource).filter(KnowledgeSource.document_id == doc.document_id).first()
    assert queried_source is not None
    assert queried_source.source_name == "Company Policy 2026"

def test_engine_initialization():
    engine, dialect = init_engine()
    assert engine is not None
    assert dialect in ("mysql", "sqlite")
