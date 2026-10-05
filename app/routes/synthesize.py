from fastapi import APIRouter, Request, BackgroundTasks, Form
from fastapi.responses import JSONResponse
import uuid, time, os
from app.config import settings

AUDIO_DIR = "output"
jobs = {}
queue = []

router = APIRouter()

@router.post("/synthesize")
def synthesize(request: Request, background_tasks: BackgroundTasks, text: str = Form(...), lang: str = Form("ru")):
    # Simple functional port, real logic in app/jobs/ later
    if len(queue) >= settings.MAX_QUEUE_SIZE:
        return JSONResponse({"error": "Queue is full"}, status_code=429)
    if len(text) > settings.MAX_TEXT_LEN:
        return JSONResponse({"error": "Text too long"}, status_code=400)
    job_id = uuid.uuid4().hex
    filename = f"{job_id}.mp3"
    job = {"created_at": time.time(), "status": "queued", "filename": filename, "lang": lang}
    jobs[job_id] = job
    queue.append({"job_id": job_id, "text": text, "lang": lang, "filename": filename})
    return {"job_id": job_id, "queue_size": len(queue)}
