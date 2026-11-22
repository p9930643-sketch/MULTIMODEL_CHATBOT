import os
import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from backend.models import Document
from backend.schemas import ChatRequest, ChatResponse, CitationItem
from core.ai_engine import ai_engine
from core.rag_engine import rag_engine
from core.safety_guardrails import safety_guardrails
from services.image_service import image_service
from services.audio_service import audio_service
from services.conversation_service import conversation_service

logger = logging.getLogger(__name__)

class MultimodalEngine:
    def process_chat_pipeline(self, db: Session, request: ChatRequest) -> ChatResponse:
        """
        Coordinates the complete lifecycle:
        1. Conversation session resolution
        2. Prompt injection & crisis safety scanning
        3. Modality dispatching (Text, Image, Audio, Document RAG)
        4. Context generation & AI synthesis
        5. Optional TTS synthesis
        6. Database message persistence
        """
        # 1. Resolve conversation
        conv = conversation_service.get_or_create_conversation(db, request.conversation_id)
        conv_id = conv.conversation_id

        user_prompt = request.message.strip()

        # Save user message
        conversation_service.add_message(
            db=db,
            conversation_id=conv_id,
            sender="user",
            content=user_prompt,
            modality=request.modality,
            metadata={"media_url": request.media_url} if request.media_url else None
        )

        # 2. Safety & Crisis check
        is_crisis, crisis_reply = safety_guardrails.detect_crisis(user_prompt)
        if is_crisis:
            bot_msg = conversation_service.add_message(
                db=db,
                conversation_id=conv_id,
                sender="assistant",
                content=crisis_reply,
                modality="text",
                metadata={"safety": "crisis_intercepted"}
            )
            return ChatResponse(
                conversation_id=conv_id,
                message_id=bot_msg.message_id,
                reply=crisis_reply,
                modality="text",
                is_crisis=True,
                is_rag_grounded=False,
                citations=[],
                audio_url=None,
                created_at=bot_msg.created_at
            )

        # 3. Prompt injection detection warning
        if safety_guardrails.detect_prompt_injection(user_prompt):
            reply_text = (
                "I detected instructions attempting to alter my safety protocols or internal persona. "
                "As an AI companion, I remain dedicated to safe, respectful, and supportive conversation. "
                "How can I help you today?"
            )
            bot_msg = conversation_service.add_message(
                db=db,
                conversation_id=conv_id,
                sender="assistant",
                content=reply_text,
                modality="text",
                metadata={"safety": "prompt_injection_flagged"}
            )
            return ChatResponse(
                conversation_id=conv_id,
                message_id=bot_msg.message_id,
                reply=reply_text,
                modality="text",
                is_crisis=False,
                is_rag_grounded=False,
                citations=[],
                audio_url=None,
                created_at=bot_msg.created_at
            )

        # 4. Modality Dispatch
        final_reply = ""
        is_grounded = False
        citations: List[CitationItem] = []

        # Case A: Image Analysis
        if request.modality == "image" and request.media_url:
            final_reply = image_service.analyze_image(
                file_path=request.media_url,
                prompt=user_prompt
            )

        # Case B: Audio Modality
        elif request.modality == "audio" and request.media_url:
            # If user message is audio, transcribe first if needed
            transcription = audio_service.transcribe_audio(request.media_url)
            effective_prompt = f"The user spoke the following audio message: \"{transcription}\"\nPlease respond empathetically and helpfully."
            final_reply = ai_engine.generate_chat_response(effective_prompt)

        # Case C: Document RAG Enabled
        elif request.use_rag:
            # Check if any documents exist
            doc_count = db.query(Document).filter(Document.processing_status == "completed").count()
            if doc_count > 0:
                final_reply, citations = rag_engine.generate_grounded_answer(
                    db=db,
                    query=user_prompt
                )
                is_grounded = len(citations) > 0
            else:
                # No documents uploaded yet; fallback to conversational AI
                history_records = conversation_service.get_conversation_messages(db, conv_id)
                formatted_history = [
                    {"sender": m.sender, "content": m.message_content}
                    for m in history_records[-6:-1]
                ]
                final_reply = ai_engine.generate_chat_response(
                    prompt=user_prompt,
                    conversation_history=formatted_history
                )

        # Case D: Standard Conversational Text
        else:
            history_records = conversation_service.get_conversation_messages(db, conv_id)
            formatted_history = [
                {"sender": m.sender, "content": m.message_content}
                for m in history_records[-6:-1]
            ]
            final_reply = ai_engine.generate_chat_response(
                prompt=user_prompt,
                conversation_history=formatted_history
            )

        # Check for health/medical themes and append disclaimer if appropriate
        final_reply = safety_guardrails.append_medical_disclaimer(
            final_reply,
            mentions_health=any(w in user_prompt.lower() for w in ["diagnos", "depression", "anxiety", "doctor", "medication", "pill", "illness", "symptom"])
        )

        # 5. Optional Speech generation
        audio_url = None
        if request.generate_speech and final_reply:
            try:
                audio_path = audio_service.synthesize_speech(final_reply)
                # Return relative endpoint path for audio download
                filename = os.path.basename(audio_path)
                audio_url = f"/speech/file/{filename}"
            except Exception as e:
                logger.warning("Could not synthesize speech: %s", e)

        # 6. Save assistant message
        bot_msg = conversation_service.add_message(
            db=db,
            conversation_id=conv_id,
            sender="assistant",
            content=final_reply,
            modality="multimodal" if audio_url else "text",
            metadata={
                "citations": [c.model_dump() for c in citations] if citations else [],
                "audio_url": audio_url
            }
        )

        return ChatResponse(
            conversation_id=conv_id,
            message_id=bot_msg.message_id,
            reply=final_reply,
            modality=bot_msg.modality,
            is_crisis=False,
            is_rag_grounded=is_grounded,
            citations=citations,
            audio_url=audio_url,
            created_at=bot_msg.created_at
        )

multimodal_engine = MultimodalEngine()
