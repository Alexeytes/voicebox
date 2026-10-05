from app.tts.gtts_engine import GTTSEngine
from app.tts.edge_engine import EdgeTTSEngine, TTSEngineUnavailable
from app.tts.base import Voice, TTSEngine
from typing import List

def get_all_engines() -> List[TTSEngine]:
    engines = []
    try:
        engines.append(GTTSEngine())
    except Exception:
        pass
    try:
        engines.append(EdgeTTSEngine())
    except Exception:
        pass
    return engines

def list_all_voices() -> List[Voice]:
    voices = []
    for engine in get_all_engines():
        try:
            voices.extend(engine.list_voices())
        except TTSEngineUnavailable:
            pass
        except Exception:
            pass
    return voices
