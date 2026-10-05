import os
import uuid
import time
import threading
from fastapi import FastAPI, Request, Form, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from starlette.rate_limiting import RateLimitMiddleware, RateLimitException
from starlette.status import HTTP_429_TOO_MANY_REQUESTS
from typing import Dict
from gtts import gTTS

# --- Configs ---
AUDIO_DIR = "output"
QUEUE_SIZE = 10
MAX_TEXT_LEN = 10000
TTL_SEC = 3600
RATE_LIMIT = (5, 60)  # 5 requests per 60 seconds per IP

# --- State ---
jobs: Dict[str, dict] = {}
queue = []
queue_lock = threading.Lock()

def ensure_audio_dir():
    if not os.path.exists(AUDIO_DIR):
        os.makedirs(AUDIO_DIR)

# --- FastAPI ---
app = FastAPI()
templates = Jinja2Templates(directory="prototype/templates")

# --- Utils ---
def cleanup_expired():
    now = time.time()
    for job_id, job in list(jobs.items()):
        if job.get("created_at", 0) + TTL_SEC < now:
            filename = job.get("filename")
            if filename:
                try:
                    os.remove(os.path.join(AUDIO_DIR, filename))
                except Exception:
                    pass
            jobs.pop(job_id, None)

def synth_worker():
    while True:
        with queue_lock:
            if queue:
                entry = queue.pop(0)
            else:
                entry = None
        if not entry:
            time.sleep(0.2)
            continue
        job_id = entry["job_id"]
        text = entry["text"]
        lang = entry["lang"]
        filename = entry["filename"]
        try:
            tts = gTTS(text=text, lang=lang)
            tts.save(os.path.join(AUDIO_DIR, filename))
            jobs[job_id]["status"] = "done"
            jobs[job_id]["url"] = f"/audio/{filename}"
        except Exception as ex:
            jobs[job_id]["status"] = "error"
            jobs[job_id]["error"] = str(ex)

# Start worker thread
t = threading.Thread(target=synth_worker, daemon=True)
t.start()

@app.on_event("startup")
def _startup():
    ensure_audio_dir()

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/synthesize")
def synthesize(request: Request, background_tasks: BackgroundTasks, text: str = Form(...), lang: str = Form("ru")):
    if len(queue) >= QUEUE_SIZE:
        return JSONResponse({"error": "Queue is full"}, status_code=429)
    if len(text) > MAX_TEXT_LEN:
        return JSONResponse({"error": "Text too long"}, status_code=400)
    job_id = uuid.uuid4().hex
    filename = f"{job_id}.mp3"
    job = {"created_at": time.time(), "status": "queued", "filename": filename, "lang": lang}
    jobs[job_id] = job
    with queue_lock:
        queue.append({"job_id": job_id, "text": text, "lang": lang, "filename": filename})
    background_tasks.add_task(cleanup_expired)
    return {"job_id": job_id, "queue_size": len(queue)}

@app.get("/status/{job_id}")
def status(job_id: str):
    job = jobs.get(job_id)
    if not job:
        return {"status": "not_found"}
    result = {k: job.get(k) for k in ["status", "error", "url"] if k in job}
    return result

@app.get("/audio/{filename}")
def get_audio(filename: str):
    if not filename.endswith(".mp3") or len(filename) != 36:
        raise HTTPException(status_code=404)
    full = os.path.join(AUDIO_DIR, filename)
    if not os.path.exists(full):
        raise HTTPException(status_code=404)
    return FileResponse(full, media_type="audio/mpeg")
