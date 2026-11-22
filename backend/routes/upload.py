import os
import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Document
from backend.schemas import FileUploadResponse
from core.config import settings
from core.safety_guardrails import safety_guardrails
from services.image_service import image_service
from services.audio_service import audio_service
from services.document_service import document_service

router = APIRouter(prefix="/upload", tags=["Uploads"])

def ensure_upload_subdirs():
    (settings.upload_path / "images").mkdir(parents=True, exist_ok=True)
    (settings.upload_path / "documents").mkdir(parents=True, exist_ok=True)
    (settings.upload_path / "audio").mkdir(parents=True, exist_ok=True)

@router.post("/image", response_model=FileUploadResponse)
async def upload_image(file: UploadFile = File(...)):
    """Upload and validate an image file (JPG, JPEG, PNG)."""
    ensure_upload_subdirs()
    filename = safety_guardrails.sanitize_filename(file.filename or "image.jpg")
    ext = Path(filename).suffix.lower()

    if ext not in image_service.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported image type. Allowed: {', '.join(image_service.ALLOWED_EXTENSIONS)}"
        )

    unique_name = f"{uuid.uuid4().hex[:8]}_{filename}"
    save_path = settings.upload_path / "images" / unique_name

    contents = await file.read()
    if len(contents) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds limit of {settings.MAX_UPLOAD_SIZE_MB}MB"
        )

    with open(save_path, "wb") as f:
        f.write(contents)

    valid, msg = image_service.validate_image_file(str(save_path))
    if not valid:
        if save_path.exists():
            save_path.unlink()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    return FileUploadResponse(
        filename=filename,
        file_type="image",
        file_size=len(contents),
        file_path=str(save_path),
        message="Image uploaded and validated successfully"
    )

@router.post("/document", response_model=FileUploadResponse)
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload and validate a document (PDF, TXT), ready for RAG ingestion."""
    ensure_upload_subdirs()
    filename = safety_guardrails.sanitize_filename(file.filename or "document.txt")
    ext = Path(filename).suffix.lower()

    if ext not in document_service.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported document format. Allowed: {', '.join(document_service.ALLOWED_EXTENSIONS)}"
        )

    unique_name = f"{uuid.uuid4().hex[:8]}_{filename}"
    save_path = settings.upload_path / "documents" / unique_name

    contents = await file.read()
    if len(contents) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds limit of {settings.MAX_UPLOAD_SIZE_MB}MB"
        )

    with open(save_path, "wb") as f:
        f.write(contents)

    valid, msg = document_service.validate_document_file(str(save_path))
    if not valid:
        if save_path.exists():
            save_path.unlink()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    # Compute hash & extract text preview
    file_hash = document_service.compute_file_hash(str(save_path))
    pages = document_service.extract_text(str(save_path))
    preview = pages[0]["text"][:300] if pages else ""

    # Register in documents table
    doc_record = Document(
        filename=filename,
        file_type=ext.replace(".", ""),
        file_size=len(contents),
        file_hash=file_hash,
        processing_status="pending"
    )
    db.add(doc_record)
    db.commit()
    db.refresh(doc_record)

    return FileUploadResponse(
        filename=filename,
        file_type="document",
        file_size=len(contents),
        file_path=str(save_path),
        document_id=doc_record.document_id,
        extracted_text_preview=preview,
        message="Document uploaded successfully. Ready for RAG ingestion."
    )

@router.post("/audio", response_model=FileUploadResponse)
async def upload_audio(file: UploadFile = File(...)):
    """Upload and validate an audio file for speech-to-text processing."""
    ensure_upload_subdirs()
    filename = safety_guardrails.sanitize_filename(file.filename or "audio.mp3")
    ext = Path(filename).suffix.lower()

    if ext not in audio_service.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported audio format. Allowed: {', '.join(audio_service.ALLOWED_EXTENSIONS)}"
        )

    unique_name = f"{uuid.uuid4().hex[:8]}_{filename}"
    save_path = settings.upload_path / "audio" / unique_name

    contents = await file.read()
    if len(contents) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds limit of {settings.MAX_UPLOAD_SIZE_MB}MB"
        )

    with open(save_path, "wb") as f:
        f.write(contents)

    valid, msg = audio_service.validate_audio_file(str(save_path))
    if not valid:
        if save_path.exists():
            save_path.unlink()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    return FileUploadResponse(
        filename=filename,
        file_type="audio",
        file_size=len(contents),
        file_path=str(save_path),
        message="Audio uploaded successfully"
    )
