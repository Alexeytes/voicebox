from __future__ import annotations

import time
import uuid

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.config import settings
from app.documents import extract_text
from app.jobs.queue import Job, queue_size, submit
from app.stats.collector import log_event

router = APIRouter()
MAX_UPLOAD_BYTES = 25 * 1024 * 1024
MAX_BOOK_CHARACTERS = 2_000_000
STYLES = {"natural", "expressive", "calm"}


@router.post("/synthesize")
async def synthesize(
    text: str = Form(""),
    lang: str = Form("ru"),
    voice_id: str = Form(""),
    style: str = Form("natural"),
    book: UploadFile | None = File(None),
):
    uploaded_book = book is not None and bool(book.filename)
    if uploaded_book:
        data = await book.read(MAX_UPLOAD_BYTES + 1)
        if len(data) > MAX_UPLOAD_BYTES:
            raise HTTPException(413, "Файл превышает ограничение 25 МБ")
        try:
            text = extract_text(book.filename, data)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
    text = text.strip()
    if lang not in {"ru", "en"}:
        raise HTTPException(400, "Поддерживаются русский и английский языки")
    if not text:
        raise HTTPException(400, "Введите текст или загрузите книгу")
    text_limit = MAX_BOOK_CHARACTERS if uploaded_book else settings.MAX_TEXT_LEN
    if len(text) > text_limit:
        raise HTTPException(400, f"Материал превышает лимит {text_limit:,} символов")
    if not voice_id:
        if settings.AZURE_SPEECH_KEY and settings.AZURE_SPEECH_REGION and lang == "ru":
            voice_id = "azure:ru-RU-Masha:MAI-Voice-2.1"
        else:
            voice_id = "edge:ru-RU-SvetlanaNeural" if lang == "ru" else "edge:en-US-AriaNeural"
    prefix = voice_id.split(":", 1)[0]
    if prefix not in {"edge", "gtts", "azure"} or len(voice_id) > 120:
        raise HTTPException(400, "Неизвестный голос")
    if prefix == "azure" and not (settings.AZURE_SPEECH_KEY and settings.AZURE_SPEECH_REGION):
        raise HTTPException(400, "Выразительные голоса Azure не настроены на сервере")
    if style not in STYLES:
        raise HTTPException(400, "Неизвестный стиль чтения")
    job = Job(id=uuid.uuid4().hex, text=text, lang=lang, voice_id=voice_id, style=style)
    await log_event("voice_selected", lang=lang, voice_id=voice_id, engine=prefix, status="ok")
    try:
        await submit(job)
    except Exception as exc:
        raise HTTPException(429, "Очередь занята. Попробуйте позже.") from exc
    return {
        "job_id": job.id,
        "queue_size": queue_size(),
        "characters": len(text),
        "words": len(text.split()),
    }


@router.get("/status/{job_id}")
def job_status(job_id: str):
    from app.jobs.queue import get_job

    job = get_job(job_id)
    if not job:
        raise HTTPException(404, "Задача не найдена или устарела")
    elapsed = max(0, int(((job.finished_at or time.time()) - job.created_at) * 1000))
    result = {
        "job_id": job.id,
        "status": job.status,
        "progress": job.progress,
        "characters": len(job.text),
        "words": len(job.text.split()),
        "elapsed_ms": elapsed,
        "estimated_audio_seconds": round(len(job.text) / 14),
    }
    if job.audio_seconds is not None:
        result["audio_seconds"] = round(job.audio_seconds, 1)
    if job.filename:
        result["url"] = f"/audio/{job.filename}"
    if job.error:
        result["error"] = job.error
    return result
