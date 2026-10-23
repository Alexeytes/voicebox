from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class Voice:
    id: str
    engine: str
    language: str
    locale: str
    gender: str
    name: str
    description: str = ""
    styles: tuple[str, ...] = ("natural",)


class TTSEngine(ABC):
    name: str
    supports_preview: bool = True

    @abstractmethod
    def list_voices(self) -> Iterable[Voice]: ...

    @abstractmethod
    async def synthesize(self, text: str, voice_id: str, style: str = "natural") -> bytes: ...
