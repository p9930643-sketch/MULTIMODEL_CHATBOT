import logging
from typing import List
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Document, DocumentChunk
from backend.schemas import DocumentListItem
from services.document_service import document_service
from core.rag_engine import rag_engine

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Knowledge & Documents"])

@router.post("/knowledge/ingest/{document_id}")
def ingest_document_for_rag(document_id: str, db: Session = Depends(get_db)):
    """
    Ingests an uploaded document into the RAG pipeline:
    Extracts text, splits into chunks, generates embeddings, and saves to database.
    """
    doc = db.query(Document).filter(Document.document_id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    # Locate file on disk
    doc_dir = Path("uploads/documents")
    matches = list(doc_dir.glob(f"*_{doc.filename}"))
    if not matches:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document file not found on disk")

    file_path = str(matches[0])

    try:
        doc.processing_status = "processing"
        db.commit()

        # 1. Extract text
        pages = document_service.extract_text(file_path)
        if not pages:
            doc.processing_status = "failed"
            doc.error_message = "Document contained no extractable text."
            db.commit()
            return {"error": doc.error_message}

        # 2. Chunk text
        chunks = document_service.chunk_text(pages)

        # 3. Ingest into RAG store with embeddings
        inserted = rag_engine.ingest_document_chunks(
            db=db,
            document_id=doc.document_id,
            document_name=doc.filename,
            chunks=chunks
        )

        doc.processing_status = "completed"
        db.commit()

        return {
            "document_id": doc.document_id,
            "filename": doc.filename,
            "status": "completed",
            "chunks_created": inserted,
            "message": f"Successfully ingested {inserted} knowledge chunks into RAG index."
        }
    except Exception as e:
        logger.error("RAG Ingestion failed: %s", e)
        doc.processing_status = "failed"
        doc.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ingestion failed: {e}")

@router.get("/documents", response_model=List[DocumentListItem])
def list_documents(db: Session = Depends(get_db)):
    """List all registered knowledge documents and their chunk counts."""
    docs = db.query(Document).order_by(Document.upload_timestamp.desc()).all()
    results = []
    for d in docs:
        chunk_count = db.query(DocumentChunk).filter(DocumentChunk.document_id == d.document_id).count()
        results.append(DocumentListItem(
            document_id=d.document_id,
            filename=d.filename,
            file_type=d.file_type,
            file_size=d.file_size,
            upload_timestamp=d.upload_timestamp,
            processing_status=d.processing_status,
            chunk_count=chunk_count
        ))
    return results

@router.delete("/documents/{document_id}")
def delete_document(document_id: str, db: Session = Depends(get_db)):
    """Delete a document and all associated chunks from RAG index."""
    doc = db.query(Document).filter(Document.document_id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).delete()
    db.delete(doc)
    db.commit()
    return {"message": f"Document '{doc.filename}' and its chunks were deleted."}
