import os
import uuid
import logging
from pathlib import Path
from typing import Tuple
from gtts import gTTS
import google.generativeai as genai
from core.config import settings
from core.ai_engine import ai_engine

logger = logging.getLogger(__name__)

class AudioService:
    ALLOWED_EXTENSIONS = {".wav", ".mp3", ".ogg", ".m4a"}

    def __init__(self):
        self.audio_cache_dir = settings.upload_path / "audio_cache"
        self.audio_cache_dir.mkdir(parents=True, exist_ok=True)

    def validate_audio_file(self, file_path: str) -> Tuple[bool, str]:
        p = Path(file_path)
        if not p.exists():
            return False, "Audio file does not exist."

        ext = p.suffix.lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            return False, f"Unsupported audio format: {ext}. Allowed: {', '.join(self.ALLOWED_EXTENSIONS)}"

        size_bytes = p.stat().st_size
        if size_bytes > settings.max_upload_bytes:
            return False, f"Audio exceeds limit of {settings.MAX_UPLOAD_SIZE_MB}MB."

        return True, "Valid audio file"

    def transcribe_audio(self, file_path: str) -> str:
        """
        Transcribes speech from audio file using Gemini audio understanding.
        """
        valid, msg = self.validate_audio_file(file_path)
        if not valid:
            return f"Audio validation failed: {msg}"

        if not ai_engine.is_configured():
            return "⚠️ Gemini API key is missing. Cannot transcribe audio without API configuration."

        try:
            # Upload audio file to Gemini File API
            uploaded_file = genai.upload_file(path=file_path)
            model = genai.GenerativeModel(model_name=settings.GEMINI_MODEL)
            prompt = "Please accurately transcribe the speech in this audio file verbatim into text. Return only the transcribed text."
            response = model.generate_content([uploaded_file, prompt])
            return response.text.strip() if response and response.text else "Could not transcribe audio."
        except Exception as e:
            logger.error("Audio transcription failed for %s: %s", file_path, e)
            return f"Speech-to-text error: {str(e)}"

    def synthesize_speech(self, text: str, lang: str = "en") -> str:
        """
        Synthesizes text into speech MP3 using gTTS.
        Returns the absolute file path to the generated MP3.
        """
        if not text or not text.strip():
            raise ValueError("Text for speech synthesis cannot be empty.")

        # Truncate to reasonable speech synthesis length (up to 1500 chars)
        clean_text = text[:1500].strip()
        filename = f"speech_{uuid.uuid4().hex[:12]}.mp3"
        out_path = self.audio_cache_dir / filename

        try:
            tts = gTTS(text=clean_text, lang=lang, slow=False)
            tts.save(str(out_path))
            return str(out_path)
        except Exception as e:
            logger.error("Text-to-speech synthesis failed: %s", e)
            raise RuntimeError(f"TTS synthesis failed: {e}")

audio_service = AudioService()
