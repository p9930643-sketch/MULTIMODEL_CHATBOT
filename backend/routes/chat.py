from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.schemas import (
    ChatRequest,
    ChatResponse,
    ConversationResponse,
    MessageResponse
)
from services.conversation_service import conversation_service
from core.multimodal_engine import multimodal_engine

router = APIRouter(tags=["Chat & Conversations"])

@router.post("/chat", response_model=ChatResponse, status_code=status.HTTP_200_OK)
def send_chat_message(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Process multimodal or text user query, evaluate safety, retrieve RAG context, and respond.
    """
    try:
        return multimodal_engine.process_chat_pipeline(db, request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while generating response: {str(e)}"
        )

@router.get("/conversations", response_model=List[ConversationResponse])
def get_conversations(db: Session = Depends(get_db)):
    """List recent conversation sessions."""
    return conversation_service.list_conversations(db)

@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
def get_conversation_history(conversation_id: str, db: Session = Depends(get_db)):
    """Fetch all chronological messages for a conversation session."""
    return conversation_service.get_conversation_messages(db, conversation_id)

@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_200_OK)
def delete_conversation_session(conversation_id: str, db: Session = Depends(get_db)):
    """Delete a conversation session and all its message history."""
    success = conversation_service.delete_conversation(db, conversation_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return {"message": "Conversation successfully deleted", "conversation_id": conversation_id}
