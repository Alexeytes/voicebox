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
        return [
            Voice(
                id=f"edge:{v['ShortName']}",
                engine=self.name,
                language=v["Locale"][:2],
                locale=v["Locale"],
                gender=v["Gender"].lower(),
                name=v["FriendlyName"],
                description=v.get("FriendlyName", ""),
            )
            for v in voices
        ]

    async def _list_voices_async(self):
        vm = await VoicesManager.create()
        return await vm.get_all_voices()

    async def synthesize(self, text: str, voice_id: str, style: str = "natural") -> bytes:
        voice = voice_id.removeprefix("edge:")
        settings = {
            "natural": ("+0%", "+0Hz"),
            "expressive": ("-3%", "+0Hz"),
            "calm": ("-8%", "+0Hz"),
        }
        rate, pitch = settings.get(style, settings["natural"])
        try:
            communicate = Communicate(text, voice, rate=rate, pitch=pitch)
            audio_chunks = []
            async for message in communicate.stream():
                if message.get("type") == "audio":
                    audio_chunks.append(message["data"])
            if not audio_chunks:
                raise TTSEngineUnavailableError("The voice service returned no audio")
            return b"".join(audio_chunks)
        except Exception as exc:
            raise TTSEngineUnavailableError from exc
