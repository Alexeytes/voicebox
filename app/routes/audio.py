from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os

router = APIRouter()
AUDIO_DIR = "output"

@router.get("/audio/{filename}")
def get_audio(filename: str):
    if not filename.endswith(".mp3") or len(filename) != 36:
        raise HTTPException(status_code=404)
    full = os.path.join(AUDIO_DIR, filename)
    if not os.path.exists(full):
        raise HTTPException(status_code=404)
    return FileResponse(full, media_type="audio/mpeg")
