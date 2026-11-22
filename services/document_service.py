import os
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple
try:
    import fitz  # PyMuPDF
except ImportError:
    import pymupdf as fitz
from core.config import settings
from core.safety_guardrails import safety_guardrails

logger = logging.getLogger(__name__)

class DocumentService:
    ALLOWED_EXTENSIONS = {".pdf", ".txt"}

    def compute_file_hash(self, file_path: str) -> str:
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for block in iter(lambda: f.read(65536), b""):
                sha256.update(block)
        return sha256.hexdigest()

    def validate_document_file(self, file_path: str) -> Tuple[bool, str]:
        p = Path(file_path)
        if not p.exists():
            return False, "Document file does not exist."

        ext = p.suffix.lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            return False, f"Unsupported document format: {ext}. Allowed: {', '.join(self.ALLOWED_EXTENSIONS)}"

        size_bytes = p.stat().st_size
        if size_bytes > settings.max_upload_bytes:
            return False, f"Document exceeds limit of {settings.MAX_UPLOAD_SIZE_MB}MB."

        return True, "Valid document"

    def extract_text(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extracts text from PDF or TXT file page-by-page.
        Returns list of dicts: [{"page": int, "text": str}]
        """
        p = Path(file_path)
        ext = p.suffix.lower()
        extracted_pages: List[Dict[str, Any]] = []

        if ext == ".txt":
            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    raw_text = f.read()
                cleaned = safety_guardrails.sanitize_untrusted_input(raw_text)
                extracted_pages.append({"page": 1, "text": cleaned})
            except Exception as e:
                logger.error("Error reading TXT file %s: %s", file_path, e)
                raise ValueError(f"Failed to read TXT file: {e}")

        elif ext == ".pdf":
            try:
                doc = fitz.open(file_path)
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    raw_text = page.get_text("text")
                    cleaned = safety_guardrails.sanitize_untrusted_input(raw_text)
                    if cleaned.strip():
                        extracted_pages.append({
                            "page": page_num + 1,
                            "text": cleaned
                        })
                doc.close()
            except Exception as e:
                logger.error("Error extracting PDF %s: %s", file_path, e)
                raise ValueError(f"Failed to parse PDF document: {e}")

        return extracted_pages

    def chunk_text(
        self,
        pages: List[Dict[str, Any]],
        chunk_size: int = 600,
        chunk_overlap: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Chunks text recursively while preserving page attribution and metadata.
        """
        chunks: List[Dict[str, Any]] = []
        chunk_idx = 0

        for page_info in pages:
            page_num = page_info["page"]
            text = page_info["text"]

            # Split into words or paragraphs
            start = 0
            text_len = len(text)

            while start < text_len:
                end = min(start + chunk_size, text_len)

                # Try to break on whitespace or punctuation if not at end
                if end < text_len:
                    last_space = text.rfind(" ", start, end)
                    if last_space > start + (chunk_size // 2):
                        end = last_space

                chunk_slice = text[start:end].strip()
                if chunk_slice:
                    chunks.append({
                        "chunk_index": chunk_idx,
                        "chunk_text": chunk_slice,
                        "metadata": {
                            "page": page_num,
                            "char_start": start,
                            "char_end": end,
                            "length": len(chunk_slice)
                        }
                    })
                    chunk_idx += 1

                start = end - chunk_overlap if end < text_len else text_len

        return chunks

document_service = DocumentService()
