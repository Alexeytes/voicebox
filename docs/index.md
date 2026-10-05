# Voicebox

**Voicebox** — автономный TTS сервис с современным API, настраиваемой админкой, статистикой и баннерной системой.

- Многоязычный синтез речи (gTTS, Edge)
- Админ-панель с метрикой, защитой, баннерами
- UI без фреймворков
- SQLite, in-memory очереди, независимость от внешних сервисов
- Docker-образ и Makefile для запуска

## Быстрый старт

```bash
git clone ...
cd voicebox
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
make run
```

Подробнее — см. разделы архитектуры, запуска, API и админки.
