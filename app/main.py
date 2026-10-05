from __future__ import annotations
from fastapi import FastAPI
from app.routes.pages import router as pages_router
from app.routes.synthesize import router as synthesize_router
from app.routes.audio import router as audio_router
from app.routes.voices import router as voices_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.include_router(pages_router)
app.include_router(synthesize_router)
app.include_router(audio_router)
app.include_router(voices_router)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
