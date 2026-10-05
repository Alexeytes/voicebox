# Prototype README

Минимальный прототип FastAPI для TTS (gTTS-based)

- POST /synthesize (form-data: text) — создать задачу
- GET /status/{job_id} — статус
- GET /audio/{filename} — получить mp3
- Очередь, 1 воркер, TTL аудио — 1 час

Для запуска:

```bash
pip install fastapi "uvicorn[standard]" gtts jinja2
uvicorn prototype.app:app --reload
```

UI: http://localhost:8000/
