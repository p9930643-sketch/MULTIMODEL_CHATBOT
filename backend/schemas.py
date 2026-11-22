from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field

class CitationItem(BaseModel):
    document_id: str
    document_name: str
    chunk_index: int
    relevance_score: float
    snippet: str

class ChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: str = Field(..., min_length=1, max_length=10000, description="User prompt or question")
    modality: str = Field(default="text", description="Input modality: text, image, document, audio, multimodal")
    media_url: Optional[str] = Field(default=None, description="Path or URL to uploaded image, audio, or document")
    use_rag: bool = Field(default=True, description="Enable RAG retrieval over uploaded documents")
    generate_speech: bool = Field(default=False, description="Whether to also synthesize speech response")

class ChatResponse(BaseModel):
    conversation_id: str
    message_id: str
    reply: str
    modality: str
    is_crisis: bool = False
    is_rag_grounded: bool = False
    citations: List[CitationItem] = []
    audio_url: Optional[str] = None
    created_at: datetime

class ConversationCreate(BaseModel):
    title: Optional[str] = "New Conversation"

class ConversationResponse(BaseModel):
    conversation_id: str
    title: str
    created_at: datetime
    updated_at: datetime

class MessageResponse(BaseModel):
    message_id: str
    conversation_id: str
    sender: str
    message_content: str
    modality: str
    metadata_json: Optional[dict[str, Any]] = None
    created_at: datetime

class FileUploadResponse(BaseModel):
    filename: str
    file_type: str
    file_size: int
    file_path: str
    document_id: Optional[str] = None
    extracted_text_preview: Optional[str] = None
    message: str

class SpeechRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=4000)
    language: str = "en"

class SpeechResponse(BaseModel):
    audio_url: str
    duration_seconds: Optional[float] = None

class DocumentListItem(BaseModel):
    document_id: str
    filename: str
    file_type: str
    file_size: int
    upload_timestamp: datetime
    processing_status: str
    chunk_count: int
