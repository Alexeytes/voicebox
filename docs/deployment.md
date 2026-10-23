# Развёртывание

## Локально

Установите Python 3.11+, FFmpeg и скопируйте .env.example в .env. Задайте обязательные секреты, затем запустите make develop и make run. Приложение слушает 127.0.0.1:8000.

## Docker

Подготовьте .env с обязательными переменными, затем запустите make docker-up. Docker Compose монтирует data/ (SQLite и баннеры) и output/ (готовые MP3), поэтому данные сохраняются при обновлении контейнера. Не монтируйте .env в публикуемый образ. Для TLS поставьте reverse proxy и установите HTTPS_ONLY=true. TRUST_PROXY включайте только за доверенным proxy.

## Ограничения текущего развёртывания

Очередь и rate limiter хранят состояние в памяти одного процесса. Не запускайте несколько реплик с локальной очередью: статус и задания между ними не общие. Для горизонтального масштаба замените очередь и SQLite на общие сервисы. Для многопользовательской нагрузки настройте резервное копирование базы, мониторинг и ограничение скорости внешнего TTS.

Uvicorn uses one worker because job and rate-limit state is process-local. The Docker image uses a multi-stage build and installs FFmpeg in the runtime stage.

## Резервная копия

Сохраните data/voicebox.db и data/banners/. Папка output/ содержит временные результаты с TTL; исключите её из резервной копии, если файлы не нужны. При чистом копировании SQLite остановите сервис или используйте SQLite backup API.

## Nginx/TLS

Поставьте reverse proxy на localhost:8000 с TLS, передавайте Host, X-Forwarded-For и X-Forwarded-Proto. Включайте TRUST_PROXY=true только за доверенным proxy, HTTPS_ONLY=true при включённом TLS. Не публикуйте порт приложения напрямую в интернет.

## systemd

Запускайте Uvicorn от отдельного системного пользователя из virtualenv; задайте WorkingDirectory к каталогу приложения, EnvironmentFile к защищённому .env, Restart=on-failure и один worker. Ограничьте права на data/ и output/.
