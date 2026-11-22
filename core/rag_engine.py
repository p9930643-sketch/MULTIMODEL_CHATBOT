import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.models import Document, DocumentChunk, KnowledgeSource
from backend.schemas import CitationItem
from core.embeddings import embedding_engine
from core.ai_engine import ai_engine
from core.safety_guardrails import safety_guardrails
from core.prompt_templates import RAG_GROUNDED_SYNTHESIS_PROMPT

logger = logging.getLogger(__name__)

class RAGEngine:
    def ingest_document_chunks(
        self,
        db: Session,
        document_id: str,
        document_name: str,
        chunks: List[Dict[str, Any]]
    ) -> int:
        """
        Stores chunks with embeddings and registers knowledge source.
        """
        # Register knowledge source
        source = KnowledgeSource(
            document_id=document_id,
            source_name=document_name,
            source_metadata={"total_chunks": len(chunks)}
        )
        db.add(source)

        inserted_count = 0
        for item in chunks:
            text = item["chunk_text"]
            # Generate 768-dim embedding
            embedding_vec = embedding_engine.generate_embedding(text)

            chunk_record = DocumentChunk(
                document_id=document_id,
                chunk_index=item["chunk_index"],
                chunk_text=text,
                embedding=embedding_vec,
                chunk_metadata=item.get("metadata", {})
            )
            db.add(chunk_record)
            inserted_count += 1

        db.commit()
        logger.info("Successfully ingested %d chunks for document %s", inserted_count, document_name)
        return inserted_count

    def retrieve_relevant_chunks(
        self,
        db: Session,
        query: str,
        top_k: int = 4
    ) -> List[CitationItem]:
        """
        Retrieves top_k most relevant chunks using semantic embedding similarity and keyword overlap.
        """
        query_vec = embedding_engine.generate_query_embedding(query)

        # Fetch all chunks (or active document chunks)
        chunks = db.query(DocumentChunk).join(Document, DocumentChunk.document_id == Document.document_id)\
                   .filter(Document.processing_status == "completed").all()

        if not chunks:
            return []

        scored_chunks = []
        for ch in chunks:
            score = 0.0
            if ch.embedding:
                score = embedding_engine.cosine_similarity(query_vec, ch.embedding)

            # Boost if query keywords appear in chunk
            lower_text = ch.chunk_text.lower()
            keyword_matches = sum(1 for word in query.lower().split() if len(word) > 3 and word in lower_text)
            final_score = score + (keyword_matches * 0.05)

            # Get document name
            doc = db.query(Document).filter(Document.document_id == ch.document_id).first()
            doc_name = doc.filename if doc else "Document"

            scored_chunks.append({
                "chunk": ch,
                "score": final_score,
                "document_name": doc_name
            })

        # Sort by score descending
        scored_chunks.sort(key=lambda x: x["score"], reverse=True)
        top_results = scored_chunks[:top_k]

        citations: List[CitationItem] = []
        for item in top_results:
            ch: DocumentChunk = item["chunk"]
            citations.append(CitationItem(
                document_id=ch.document_id,
                document_name=item["document_name"],
                chunk_index=ch.chunk_index,
                relevance_score=round(item["score"], 3),
                snippet=ch.chunk_text[:250] + ("..." if len(ch.chunk_text) > 250 else "")
            ))

        return citations

    def generate_grounded_answer(
        self,
        db: Session,
        query: str,
        top_k: int = 4
    ) -> tuple[str, List[CitationItem]]:
        """
        Retrieves relevant context, constructs untrusted boundaries, and queries the LLM.
        """
        citations = self.retrieve_relevant_chunks(db, query, top_k=top_k)

        if not citations:
            return (
                "No relevant documents were found in the knowledge base to answer this question. "
                "Please upload a related document first.",
                []
            )

        # Build untrusted delimiter block
        context_parts = []
        for i, cit in enumerate(citations, 1):
            # Fetch full chunk text
            chunk_obj = db.query(DocumentChunk).filter(
                DocumentChunk.document_id == cit.document_id,
                DocumentChunk.chunk_index == cit.chunk_index
            ).first()
            content = chunk_obj.chunk_text if chunk_obj else cit.snippet
            sanitized_content = safety_guardrails.sanitize_untrusted_input(content)

            context_parts.append(
                f'<<<UNTRUSTED_DOCUMENT_CHUNK id="{i}" doc="{cit.document_name}" chunk="{cit.chunk_index}">\n'
                f"{sanitized_content}\n"
                f'</<<UNTRUSTED_DOCUMENT_CHUNK>'
            )

        joined_context = "\n\n".join(context_parts)
        prompt = RAG_GROUNDED_SYNTHESIS_PROMPT.format(
            retrieved_context=joined_context,
            user_query=query
        )

        reply = ai_engine.generate_chat_response(
            prompt=prompt,
            conversation_history=None,
            system_instruction="You are a strict, grounded knowledge assistant. Base answers only on provided untrusted document chunks."
        )

        return reply, citations

rag_engine = RAGEngine()
