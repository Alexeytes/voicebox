from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path

from pydub import AudioSegment

from app.config import settings
from app.stats.collector import log_event
from app.tts.registry import engine_for_voice
from app.tts.utils import split_text

logger = logging.getLogger(__name__)
AUDIO_DIR = Path(__file__).resolve().parents[2] / "output"


@dataclass
class Job:
    id: str
    text: str
    lang: str
    voice_id: str
    style: str = "natural"
    status: str = "queued"
    progress: int = 0
    filename: str | None = None
    error: str | None = None
    audio_seconds: float | None = None
    created_at: float = field(default_factory=time.time)
    finished_at: float | None = None


_jobs: dict[str, Job] = {}
_queue: asyncio.Queue[Job] | None = None
_workers: list[asyncio.Task] = []
_cleanup_task: asyncio.Task | None = None


async def start_workers() -> None:
    global _queue, _workers, _cleanup_task
    os.makedirs(AUDIO_DIR, exist_ok=True)
    _queue = asyncio.Queue(maxsize=settings.MAX_QUEUE_SIZE)
    _workers = [asyncio.create_task(_worker()) for _ in range(max(1, settings.NUM_WORKERS))]
    _cleanup_task = asyncio.create_task(_cleanup_expired())


async def stop_workers() -> None:
    global _cleanup_task
    if _cleanup_task:
        _cleanup_task.cancel()
        await asyncio.gather(_cleanup_task, return_exceptions=True)
        _cleanup_task = None
    for task in _workers:
        task.cancel()
    await asyncio.gather(*_workers, return_exceptions=True)
    _workers.clear()


async def submit(job: Job) -> None:
    if _queue is None:
        raise RuntimeError("Synthesis queue is not running")
    _queue.put_nowait(job)
    _jobs[job.id] = job


def get_job(job_id: str) -> Job | None:
    return _jobs.get(job_id)


def queue_size() -> int:
    return _queue.qsize() if _queue else 0


async def _cleanup_expired() -> None:
    while True:
        await asyncio.sleep(max(30, settings.CLEANUP_INTERVAL))
        now = time.time()
        preview_dir = os.path.join(AUDIO_DIR, "preview")
        if os.path.isdir(preview_dir):
            for filename in os.listdir(preview_dir):
                path = os.path.join(preview_dir, filename)
                try:
                    if now - os.path.getmtime(path) > 86400:
                        os.remove(path)
                except FileNotFoundError:
                    pass
        for job_id, job in list(_jobs.items()):
            if job.finished_at and now - job.finished_at > settings.JOB_TTL_SEC:
                _jobs.pop(job_id, None)
                if job.filename:
                    try:
                        os.remove(os.path.join(AUDIO_DIR, job.filename))
                    except FileNotFoundError:
                        pass


async def _worker() -> None:
    assert _queue is not None
    while True:
        job = await _queue.get()
        try:
            job.status = "processing"
            parts = split_text(job.text)
            engine = engine_for_voice(job.voice_id)
            combined = AudioSegment.empty()
            for index, part in enumerate(parts):
                audio = await asyncio.wait_for(
                    engine.synthesize(part, job.voice_id, style=job.style),
                    settings.SYNTHESIS_TIMEOUT,
                )
                if index:
                    combined += AudioSegment.silent(duration=120)
                segment = await asyncio.to_thread(
                    AudioSegment.from_file, BytesIO(audio), format="mp3"
                )
                combined += segment
                job.progress = int((index + 1) * 100 / len(parts))
            job.audio_seconds = len(combined) / 1000
            output = os.path.join(AUDIO_DIR, f"{job.id}.mp3")
            temporary_output = output + ".tmp"
            try:
                await asyncio.to_thread(
                    combined.export, temporary_output, format="mp3", bitrate="192k"
                )
                os.replace(temporary_output, output)
            finally:
                if os.path.exists(temporary_output):
                    os.remove(temporary_output)
            job.filename = f"{job.id}.mp3"
            job.status = "done"
            try:
                await log_event(
                    "synthesis_done",
                    lang=job.lang,
                    voice_id=job.voice_id,
                    engine=job.voice_id.split(":", 1)[0],
                    duration_ms=int((time.time() - job.created_at) * 1000),
                    status="ok",
                )
            except Exception:
                logger.exception("Could not persist TTS completion event for %s", job.id)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("TTS job %s failed", job.id)
            job.status = "error"
            job.error = (
                "Сервис не смог синтезировать аудио. Проверьте подключение и выбранный голос."
            )
            try:
                await log_event(
                    "synthesis_error",
                    lang=job.lang,
                    voice_id=job.voice_id,
                    engine=job.voice_id.split(":", 1)[0],
                    duration_ms=int((time.time() - job.created_at) * 1000),
                    status="error",
                )
            except Exception:
                logger.exception("Could not persist TTS failure event for %s", job.id)
        finally:
            job.finished_at = time.time() if job.status in {"done", "error"} else None
            _queue.task_done()
