from __future__ import annotations

import re
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter()
AUDIO_DIR = Path(__file__).resolve().parents[2] / "output"


@router.get("/audio/{filename}")
def get_audio(filename: str):
    if not re.fullmatch(r"[a-f0-9]{32}\.mp3", filename):
        raise HTTPException(status_code=404)
    path = AUDIO_DIR / filename
    if not path.is_file():
        raise HTTPException(status_code=404)
    return FileResponse(path, media_type="audio/mpeg")
