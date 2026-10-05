from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_root():
    r = client.get("/")
    assert r.status_code == 200
    assert "Генерация речи" in r.text

def test_voices():
    r = client.get("/voices")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert any('id' in v for v in data)

def test_voice_preview():
    voices = client.get("/voices").json()
    v_id = voices[0]['id']
    r = client.post("/voices/preview", data={'voice_id': v_id})
    assert r.status_code == 200
    assert r.headers['content-type'].startswith('audio/')
