# Stage 1: Builder
FROM python:3.12-slim as builder
WORKDIR /app
COPY . .
RUN apt-get update && apt-get install -y ffmpeg && python3 -m venv /venv \
  && /venv/bin/pip install --upgrade pip \
  && /venv/bin/pip install fastapi "uvicorn[standard]" jinja2 python-multipart gtts pydub pydantic-settings "passlib[bcrypt]" itsdangerous aiosqlite bleach edge-tts pytest httpx2

# Stage 2: Runtime
FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /app .
COPY --from=builder /venv /venv
ENV PATH="/venv/bin:$PATH"
RUN apt-get update && apt-get install -y ffmpeg
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
