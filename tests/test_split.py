from app.config import settings
from app.tts.utils import split_text


def test_split_short():
    text = "Привет, как дела?"
    parts = split_text(text)
    assert len(parts) == 1
    assert parts[0] == text

def test_split_long_roundtrip():
    text = "a " * 4001  # 8002 символа
    parts = split_text(text)
    assert len(parts) >= 3
    assert all(len(p) <= settings.MAX_CHUNK_LEN for p in parts)
    assert "".join(parts) == text

def test_split_preserves_all_characters():
    text = "Первое предложение. Второе! Третье? " * 500
    parts = split_text(text)
    assert "".join(parts) == text
    assert all(len(p) <= settings.MAX_CHUNK_LEN for p in parts)

def test_split_long_word_cut_hard():
    # Одно слово длиннее лимита — режем жёстко.
    text = "x" * (settings.MAX_CHUNK_LEN * 2 + 500)
    parts = split_text(text)
    assert all(len(p) <= settings.MAX_CHUNK_LEN for p in parts)
    assert "".join(parts) == text
