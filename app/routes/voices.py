from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import time
from pathlib import Path

from fastapi import APIRouter, Form, HTTPException, Query
from fastapi.responses import FileResponse

from app.config import settings
from app.stats.collector import log_event
from app.tts.registry import engine_for_voice, list_all_voices

logger = logging.getLogger(__name__)
router = APIRouter()
PREVIEW_DIR = Path(__file__).resolve().parents[2] / "output" / "preview"
os.makedirs(PREVIEW_DIR, exist_ok=True)
PREVIEW_TEXT = {
    "ru": "Здравствуйте! Это пример естественного чтения выбранным голосом.",
    "en": "Hello! This is a natural preview of the selected voice.",
}


@router.get("/voices")
def get_voices(lang: str | None = Query(None)):
    voices = list_all_voices()
    if lang:
        voices = [voice for voice in voices if voice.language == lang]
    if not voices and lang in {"ru", "en"}:
        from app.tts.gtts_engine import GTTSEngine

        voices = [voice for voice in GTTSEngine().list_voices() if voice.language == lang]
    return [
        {
            "id": voice.id,
            "engine": voice.engine,
            "language": voice.language,
            "locale": voice.locale,
            "gender": voice.gender,
            "name": voice.name,
            "description": voice.description,
            "styles": list(voice.styles),
        }
        for voice in voices
    ]


@router.post("/voices/preview")
async def voice_preview(voice_id: str = Form(...), style: str = Form("natural")):
    voices = await asyncio.to_thread(list_all_voices)
    voice = next((voice for voice in voices if voice.id == voice_id), None)
    if not voice:
        raise HTTPException(400, "Неизвестный или недоступный голос")
    if style not in {"natural", "expressive", "calm"}:
        raise HTTPException(400, "Unknown reading style")
    text = PREVIEW_TEXT.get(voice.language, PREVIEW_TEXT["en"])
    filename = hashlib.sha256(f"{voice_id}:{style}:{text}".encode()).hexdigest() + ".mp3"
    path = os.path.join(PREVIEW_DIR, filename)
    if not os.path.exists(path) or time.time() - os.path.getmtime(path) > 86400:
        try:
            audio = await asyncio.wait_for(
                engine_for_voice(voice_id).synthesize(text, voice_id, style=style),
                settings.PREVIEW_TIMEOUT,
            )
        except Exception as exc:
            logger.exception("Voice preview failed for %s", voice_id)
            raise HTTPException(503, "Не удалось создать превью этого голоса") from exc
        PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as stream:
            stream.write(audio)
    await log_event("preview_done", voice_id=voice_id, engine=voice.engine, status="ok")
    return FileResponse(path, media_type="audio/mpeg")
