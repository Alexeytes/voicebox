# API Reference

Public interface runs on the same origin as the web client. Uploaded books are limited to 25 MiB; extracted book text is limited to 2,000,000 characters. Pasted text uses MAX_TEXT_LEN (10,000 by default). Supported uploads: TXT, searchable PDF, DOCX, EPUB, FB2, ODT, HTML, RTF and Markdown. Image-only/scanned PDF requires OCR and is not currently extracted.

## Public API

- GET / — reading and upload interface.
- GET /voices?lang=ru — available voices, engine and supported styles.
- POST /voices/preview — multipart fields voice_id, optional style (natural, expressive, calm); returns MP3.
- POST /synthesize — multipart text or book, lang, voice_id, style; returns job_id.
- GET /status/{job_id} — queue status, percent, word count, elapsed time and final audio URL.
- GET /audio/{job_id}.mp3 — generated MP3.
- GET /public-settings — public language, ad rotation interval and announcement settings.
- GET /ads?position=top|between|sidebar|bottom — one weighted active sponsored banner for a page slot.
- GET /go/banner/{id} — counted banner click and safe HTTP(S) redirect.

Example curl: curl -F book=@chapter.epub -F lang=ru -F voice_id=edge:ru-RU-SvetlanaNeural -F style=natural http://localhost:8000/synthesize

## Admin API

Authenticate at /admin/login; the signed, HttpOnly session is used by the endpoints below.

- GET /admin/stats — HTML dashboard. GET /admin/api/stats/overview, timeseries, events and export.csv — protected analytics API.
- GET /admin/banners — list campaigns.
- POST /admin/banners/upload — multipart image upload (PNG/JPEG/GIF/WebP, max 2 MiB).
- POST /admin/banners — multipart title, image_url, target_url, alt_text, weight, position and optional schedule/creative.
- PATCH /admin/banners/{id} — update enabled state, weight, position or schedule.
- DELETE /admin/banners/{id} — remove campaign.

Bootstrap the first administrator with python -m app.admin.cli bootstrap after setting ADMIN_USERNAME and ADMIN_PASSWORD in .env.
