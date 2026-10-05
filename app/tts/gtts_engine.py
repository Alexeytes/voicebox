from __future__ import annotations

import asyncio
from collections.abc import Iterable

from gtts import gTTS

from app.tts.base import TTSEngine, Voice


class GTTSEngine(TTSEngine):
    name = "gtts"
    supports_preview = True
    _default_voices = [
        Voice(
            id="gtts:ru",
            engine="gtts",
            language="ru",
            locale="ru-RU",
            gender="female",
            name="Google Russian Female",
            description="Google TTS Russian",
        ),
        Voice(
            id="gtts:en",
            engine="gtts",
            language="en",
            locale="en-US",
            gender="female",
            name="Google English Female",
            description="Google TTS English",
        ),
    ]
    def list_voices(self) -> Iterable[Voice]:
        return self._default_voices

    async def synthesize(self, text: str, voice_id: str) -> bytes:
        lang = None
        for v in self._default_voices:
            if v.id == voice_id:
                lang = v.language
                break
        if not lang:
            raise ValueError(f"Unknown voice_id: {voice_id}")
        def do_synth(text, lang):
            tts = gTTS(text=text, lang=lang)
            from io import BytesIO
            buf = BytesIO()
            tts.write_to_fp(buf)
            return buf.getvalue()
        return await asyncio.to_thread(do_synth, text, lang)
