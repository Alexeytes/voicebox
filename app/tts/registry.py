
import contextlib

from app.tts.base import TTSEngine, Voice
from app.tts.edge_engine import EdgeTTSEngine, TTSEngineUnavailableError
from app.tts.gtts_engine import GTTSEngine


def get_all_engines() -> list[TTSEngine]:
    engines = []
    with contextlib.suppress(Exception):
        engines.append(GTTSEngine())
    with contextlib.suppress(Exception):
        engines.append(EdgeTTSEngine())
    return engines

def list_all_voices() -> list[Voice]:
    voices = []
    for engine in get_all_engines():
        try:
            voices.extend(engine.list_voices())
        except TTSEngineUnavailableError:
            pass
        except Exception:
            pass
    return voices
