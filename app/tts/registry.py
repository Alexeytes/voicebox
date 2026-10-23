from __future__ import annotations

from functools import lru_cache

from app.tts.azure_engine import AzureSpeechEngine
from app.tts.base import TTSEngine, Voice
from app.tts.edge_engine import EdgeTTSEngine
from app.tts.gtts_engine import GTTSEngine


def get_all_engines() -> list[TTSEngine]:
    return [EdgeTTSEngine(), AzureSpeechEngine(), GTTSEngine()]


def engine_for_voice(voice_id: str) -> TTSEngine:
    if voice_id.startswith("azure:"):
        return AzureSpeechEngine()
    if voice_id.startswith("edge:"):
        return EdgeTTSEngine()
    if voice_id.startswith("gtts:"):
        return GTTSEngine()
    raise ValueError("Неизвестный голос")


@lru_cache(maxsize=1)
def _cached_voices() -> tuple[Voice, ...]:
    voices: list[Voice] = []
    for engine in get_all_engines():
        try:
            voices.extend(engine.list_voices())
        except Exception:
            continue
    return tuple(voices)


def list_all_voices() -> list[Voice]:
    return list(_cached_voices())
