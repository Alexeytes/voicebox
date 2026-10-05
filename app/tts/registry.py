from app.tts.gtts_engine import GTTSEngine
from app.tts.base import Voice, TTSEngine
from typing import List

# Возможность расширения на другие движки (edge-tts ...)
def get_all_engines() -> List[TTSEngine]:
    engines = []
    try:
        engines.append(GTTSEngine())
    except Exception:
        pass  # Логировать в будущем
    return engines

def list_all_voices() -> List[Voice]:
    voices = []
    for engine in get_all_engines():
        try:
            voices.extend(engine.list_voices())
        except Exception:
            pass
    return voices
