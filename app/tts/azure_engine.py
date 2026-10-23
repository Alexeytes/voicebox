from __future__ import annotations

import asyncio
from collections.abc import Iterable
from xml.sax.saxutils import escape

from app.config import settings
from app.tts.base import TTSEngine, Voice

STYLES = {"natural": "neutral", "expressive": "reflective", "calm": "serious"}


class AzureSpeechEngine(TTSEngine):
    name = "azure-speech"
    supports_preview = True

    def list_voices(self) -> Iterable[Voice]:
        if not settings.AZURE_SPEECH_KEY or not settings.AZURE_SPEECH_REGION:
            return []
        voices = [
            ("ru-RU-Masha:MAI-Voice-2.1", "ru", "female", "Маша · выразительный нейроголос"),
            ("ru-RU-Lev:MAI-Voice-2.1", "ru", "male", "Лев · выразительный нейроголос"),
        ]
        return [
            Voice(
                id=f"azure:{name}",
                engine=self.name,
                language=lang,
                locale=name.split("-")[0] + "-" + name.split("-")[1],
                gender=gender,
                name=label,
                description="Нейроголос Microsoft с управляемой интонацией",
                styles=("natural", "expressive", "calm"),
            )
            for name, lang, gender, label in voices
        ]

    async def synthesize(self, text: str, voice_id: str, style: str = "natural") -> bytes:
        if not settings.AZURE_SPEECH_KEY or not settings.AZURE_SPEECH_REGION:
            raise RuntimeError("Azure Speech не настроен")
        try:
            import azure.cognitiveservices.speech as speechsdk
        except ImportError as exc:
            raise RuntimeError("Установите azure-cognitiveservices-speech") from exc
        voice = voice_id.removeprefix("azure:")
        azure_style = STYLES.get(style, "neutral")
        ssml = (
            f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" '
            f'xmlns:mstts="http://www.w3.org/2001/mstts" xml:lang="ru-RU">'
            f'<voice name="{escape(voice)}"><mstts:express-as style="{azure_style}" styledegree="1.1">'
            f"{escape(text)}</mstts:express-as></voice></speak>"
        )

        def _synthesize() -> bytes:
            speech_config = speechsdk.SpeechConfig(
                subscription=settings.AZURE_SPEECH_KEY, region=settings.AZURE_SPEECH_REGION
            )
            speech_config.set_speech_synthesis_output_format(
                speechsdk.SpeechSynthesisOutputFormat.Audio24Khz48KBitRateMonoMp3
            )
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=speech_config, audio_config=None
            )
            result = synthesizer.speak_ssml_async(ssml).get()
            if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
                details = (
                    result.cancellation_details.error_details
                    if result.cancellation_details
                    else "Unknown synthesis error"
                )
                raise RuntimeError(details)
            return result.audio_data

        return await asyncio.to_thread(_synthesize)
