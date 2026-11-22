from pathlib import Path
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from backend.schemas import SpeechRequest, SpeechResponse
from services.audio_service import audio_service

router = APIRouter(prefix="/speech", tags=["Speech & Audio"])

@router.post("/generate", response_model=SpeechResponse)
def generate_speech(request: SpeechRequest):
    """Generate audio speech from text prompt using TTS."""
    try:
        mp3_path = audio_service.synthesize_speech(request.text, lang=request.language)
        filename = Path(mp3_path).name
        return SpeechResponse(
            audio_url=f"/speech/file/{filename}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Speech synthesis failed: {str(e)}"
        )

@router.get("/file/{filename}")
def stream_speech_file(filename: str):
    """Stream generated MP3 audio file."""
    file_path = audio_service.audio_cache_dir / filename
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audio file not found")
    return FileResponse(path=str(file_path), media_type="audio/mpeg", filename=filename)
