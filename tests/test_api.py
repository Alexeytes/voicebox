import pytest
from fastapi.testclient import TestClient

from app.db import database
from app.main import app
from app.routes import voices as voice_routes
from app.tts.base import Voice


@pytest.fixture
def client(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    monkeypatch.setattr(database, "DATA_DIR", data_dir)
    monkeypatch.setattr(database, "DB_FILE", data_dir / "voicebox.db")
    monkeypatch.setattr(voice_routes, "PREVIEW_DIR", tmp_path / "preview")
    voice = Voice(
        id="gtts:ru", engine="gtts", language="ru", locale="ru-RU",
        gender="female", name="Test voice",
    )
    monkeypatch.setattr(voice_routes, "list_all_voices", lambda: [voice])

    class FakeEngine:
        async def synthesize(self, text, voice_id, style="natural"):
            return b"ID3-test-audio"

    monkeypatch.setattr(voice_routes, "engine_for_voice", lambda voice_id: FakeEngine())
    with TestClient(app) as test_client:
        yield test_client


def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Пусть книга" in response.text
    assert "Недавние аудио" in response.text


def test_voices(client):
    response = client.get("/voices")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["id"] == "gtts:ru"


def test_voice_preview(client):
    response = client.post("/voices/preview", data={"voice_id": "gtts:ru"})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("audio/")
    assert response.content == b"ID3-test-audio"
