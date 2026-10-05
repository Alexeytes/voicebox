from __future__ import annotations

import asyncio
from collections.abc import Iterable

from edge_tts import Communicate, VoicesManager

from app.tts.base import TTSEngine, Voice


class TTSEngineUnavailableError(Exception):
    pass

class EdgeTTSEngine(TTSEngine):
    name = "edge-tts"
    supports_preview = True

    def list_voices(self) -> Iterable[Voice]:
        try:
            voices = asyncio.run(self._list_voices_async())
        except Exception as err:
            raise TTSEngineUnavailableError from err
        return [Voice(id=f"edge:{v['ShortName']}", engine=self.name, language=v['Locale'][:2],
                      locale=v['Locale'], gender=v['Gender'].lower(), name=v['ShortName'], description=v['FriendlyName'])
                for v in voices]
    async def _list_voices_async(self):
        vm = await VoicesManager.create()
        return await vm.get_all_voices()

    async def synthesize(self, text: str, voice_id: str) -> bytes:
        voice = voice_id.removeprefix("edge:")
        try:
            communicate = Communicate(text, voice)
            return b"".join([c async for c, _ in communicate.stream()])
        except Exception as e:
            # 403 (no quota/region fail), NoAudioReceived, etc
            raise TTSEngineUnavailableError from e
