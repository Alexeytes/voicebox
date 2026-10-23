from __future__ import annotations

import re

from app.config import settings

# Границы предложений: точка/!/?/… + пробел, либо двойной перевод строки.
# Используем lookbehind, чтобы разделитель остался в конце предыдущего предложения.
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?…])\s+|\n\n")


def split_text(text: str) -> list[str]:
    """Разбивает текст на части по MAX_CHUNK_LEN, стараясь резать по границам предложений.

    Гарантии:
      * каждая часть длиной <= MAX_CHUNK_LEN;
      * "".join(parts) == text — ни один символ не потерян.
    """
    max_len = settings.MAX_CHUNK_LEN
    if len(text) <= max_len:
        return [text]

    # Разбиваем на предложения, сохраняя разделители в предыдущем куске.
    sentences: list[str] = []
    start = 0
    for m in _SENTENCE_SPLIT.finditer(text):
        sentences.append(text[start : m.end()])
        start = m.end()
    if start < len(text):
        sentences.append(text[start:])

    # Складываем предложения в части, не превышая max_len.
    parts: list[str] = []
    buf = ""
    for sentence in sentences:
        if len(sentence) > max_len:
            # Предложение само длиннее лимита — сначала сбрасываем буфер,
            # потом режем жёстко по символам.
            if buf:
                parts.append(buf)
                buf = ""
            for i in range(0, len(sentence), max_len):
                parts.append(sentence[i : i + max_len])
            continue

        if len(buf) + len(sentence) > max_len:
            parts.append(buf)
            buf = sentence
        else:
            buf += sentence

    if buf:
        parts.append(buf)

    return parts
