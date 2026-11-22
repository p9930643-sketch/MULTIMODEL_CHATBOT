import logging
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from backend.models import Conversation, Message
from backend.schemas import MessageResponse, ConversationResponse

logger = logging.getLogger(__name__)

class ConversationService:
    def get_or_create_conversation(self, db: Session, conversation_id: Optional[str] = None) -> Conversation:
        if conversation_id:
            conv = db.query(Conversation).filter(Conversation.conversation_id == conversation_id).first()
            if conv:
                return conv

        # Create new conversation
        new_conv = Conversation(title="New Conversation")
        db.add(new_conv)
        db.commit()
        db.refresh(new_conv)
        return new_conv

    def list_conversations(self, db: Session, limit: int = 50) -> List[ConversationResponse]:
        convs = db.query(Conversation).order_by(Conversation.updated_at.desc()).limit(limit).all()
        return [
            ConversationResponse(
                conversation_id=c.conversation_id,
                title=c.title,
                created_at=c.created_at,
                updated_at=c.updated_at
            ) for c in convs
        ]

    def get_conversation_messages(self, db: Session, conversation_id: str) -> List[MessageResponse]:
        msgs = db.query(Message).filter(Message.conversation_id == conversation_id)\
                 .order_by(Message.created_at.asc()).all()
        return [
            MessageResponse(
                message_id=m.message_id,
                conversation_id=m.conversation_id,
                sender=m.sender,
                message_content=m.message_content,
                modality=m.modality,
                metadata_json=m.metadata_json,
                created_at=m.created_at
            ) for m in msgs
        ]

    def add_message(
        self,
        db: Session,
        conversation_id: str,
        sender: str,
        content: str,
        modality: str = "text",
        metadata: Optional[dict] = None
    ) -> Message:
        msg = Message(
            conversation_id=conversation_id,
            sender=sender,
            message_content=content,
            modality=modality,
            metadata_json=metadata
        )
        db.add(msg)

        # Update conversation title from first user message if still default
        conv = db.query(Conversation).filter(Conversation.conversation_id == conversation_id).first()
        if conv:
            conv.updated_at = datetime.utcnow()
            if conv.title == "New Conversation" and sender == "user":
                clean_title = content.strip().replace("\n", " ")[:40]
                conv.title = clean_title + ("..." if len(content) > 40 else "")

        db.commit()
        db.refresh(msg)
        return msg

    def delete_conversation(self, db: Session, conversation_id: str) -> bool:
        conv = db.query(Conversation).filter(Conversation.conversation_id == conversation_id).first()
        if not conv:
            return False
        # Delete associated messages first for robust cascade across SQLite & MySQL
        db.query(Message).filter(Message.conversation_id == conversation_id).delete()
        db.delete(conv)
        db.commit()
        return True

conversation_service = ConversationService()
