import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, JSON
from backend.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class Conversation(Base):
    __tablename__ = "conversations"

    conversation_id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(255), nullable=False, default="New Conversation")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class Message(Base):
    __tablename__ = "messages"

    message_id = Column(String(36), primary_key=True, default=generate_uuid)
    conversation_id = Column(String(36), ForeignKey("conversations.conversation_id", ondelete="CASCADE"), nullable=False)
    sender = Column(String(20), nullable=False)  # user, assistant, system
    message_content = Column(Text, nullable=False)
    modality = Column(String(30), nullable=False, default="text")  # text, image, document, audio, multimodal
    metadata_json = Column(JSON, nullable=True)  # citations, media links, safety flags
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class Document(Base):
    __tablename__ = "documents"

    document_id = Column(String(36), primary_key=True, default=generate_uuid)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_hash = Column(String(64), nullable=False)
    upload_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    processing_status = Column(String(30), nullable=False, default="pending")  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    chunk_id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.document_id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    embedding = Column(JSON, nullable=True)  # Array of floats
    chunk_metadata = Column(JSON, nullable=True)

class KnowledgeSource(Base):
    __tablename__ = "knowledge_sources"

    source_id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.document_id", ondelete="CASCADE"), nullable=False)
    source_name = Column(String(255), nullable=False)
    source_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
