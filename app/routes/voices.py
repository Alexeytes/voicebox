import hashlib
import os
import time

from fastapi import APIRouter, BackgroundTasks, Form, Query, Request
from fastapi.responses import FileResponse, JSONResponse

from app.tts.gtts_engine import GTTSEngine
from app.tts.registry import list_all_voices

router = APIRouter()
PREVIEW_DIR = "output/preview"

os.makedirs(PREVIEW_DIR, exist_ok=True)

@router.get("/voices")
def get_voices(lang: str = Query(None)):
    voices = list_all_voices()
    if lang:
        voices = [v for v in voices if v.language == lang]
    res = [{
        "id": v.id,
        "engine": v.engine,
        "language": v.language,
        "locale": v.locale,
        "gender": v.gender,
        "name": v.name,
        "description": v.description,
    } for v in voices]
    return JSONResponse(res)

# Короткая фраза для превью (фиксировано)
PREVIEW_TEXT = {
    "ru": "Это тестовое превью голоса.",
    "en": "This is a voice preview.",
}

@router.post("/voices/preview")
def voice_preview(request: Request, background_tasks: BackgroundTasks, voice_id: str = Form(...)):
    # Параметры и ограничения — rate limit делается на уровне middleware позже
    engine = GTTSEngine()
    voice = next((v for v in engine.list_voices() if v.id == voice_id), None)
    if not voice:
        return JSONResponse({"error": "Unknown voice_id"}, status_code=400)
    text = PREVIEW_TEXT.get(voice.language, PREVIEW_TEXT["en"])
    h = hashlib.md5(f"{voice_id}:{text}".encode()).hexdigest()
    fname = f"{h}.mp3"
    fpath = os.path.join(PREVIEW_DIR, fname)
    # Кеш на диск 24 часа
    if not os.path.exists(fpath) or (time.time() - os.path.getmtime(fpath)) > 60*60*24:
        # Генерируем превью
        data = engine.synthesize(text, voice_id)
        import asyncio
        if asyncio.iscoroutine(data):
            data = asyncio.run(data)
        with open(fpath, "wb") as f:
            f.write(data)
    return FileResponse(fpath, media_type="audio/mpeg")
