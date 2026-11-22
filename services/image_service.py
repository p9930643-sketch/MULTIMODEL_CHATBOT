import os
import logging
from pathlib import Path
from PIL import Image
from core.ai_engine import ai_engine
from core.config import settings
from core.safety_guardrails import safety_guardrails

logger = logging.getLogger(__name__)

class ImageService:
    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}

    def validate_image_file(self, file_path: str) -> tuple[bool, str]:
        p = Path(file_path)
        if not p.exists():
            return False, "File does not exist."

        ext = p.suffix.lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            return False, f"Unsupported image format: {ext}. Allowed formats: {', '.join(self.ALLOWED_EXTENSIONS)}"

        size_bytes = p.stat().st_size
        if size_bytes > settings.max_upload_bytes:
            return False, f"Image size exceeds maximum limit of {settings.MAX_UPLOAD_SIZE_MB}MB."

        try:
            with Image.open(file_path) as img:
                img.verify()
        except Exception as e:
            return False, f"Corrupted or invalid image file: {e}"

        return True, "Valid image"

    def analyze_image(self, file_path: str, prompt: str = "Please describe this image and provide insights.") -> str:
        valid, msg = self.validate_image_file(file_path)
        if not valid:
            return f"Image validation failed: {msg}"

        try:
            with Image.open(file_path) as img:
                # Convert RGBA or CMYK to RGB if needed
                if img.mode not in ("RGB", "L"):
                    img = img.convert("RGB")
                return ai_engine.generate_multimodal_response(
                    prompt=prompt,
                    media_parts=[img]
                )
        except Exception as e:
            logger.error("Failed to process image %s: %s", file_path, e)
            return f"Failed to analyze image: {str(e)}"

image_service = ImageService()
