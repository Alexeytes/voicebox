# Быстрый запуск

Для запуска нужны Python 3.11+, FFmpeg и доступ к сети для Edge TTS.

1. Создайте виртуальное окружение и установите проект вместе с инструментами разработки:

   ```sh
   python -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev]"
   ```

2. Создайте локальный файл конфигурации и задайте длинные случайные секреты:

   ```sh
   cp .env.example .env
   ```

   Обязательные параметры описаны в [конфигурации](configuration.md).

3. Запустите сервер:

   ```sh
   make run
   ```

Откройте http://127.0.0.1:8000. Для первого администратора выполните `python -m app.admin bootstrap` после настройки `ADMIN_USERNAME` и `ADMIN_PASSWORD`.

Перед production-развёртыванием прочитайте [инструкцию развёртывания](deployment.md).
