from __future__ import annotations

import json
import re
import uuid
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

import bleach
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.auth.sessions import require_admin
from app.db.database import get_db
from app.stats.collector import log_event

router = APIRouter()
BANNER_DIR = Path(__file__).resolve().parents[2] / "data" / "banners"
MAX_IMAGE_SIZE = 2 * 1024 * 1024
POSITIONS = {"top", "sidebar", "between", "bottom"}
MIMES = {
    b"\x89PNG\r\n\x1a\n": ("png", "image/png"),
    b"\xff\xd8\xff": ("jpg", "image/jpeg"),
    b"GIF87a": ("gif", "image/gif"),
    b"GIF89a": ("gif", "image/gif"),
    b"RIFF": ("webp", "image/webp"),
}
_ALLOWED_TAGS = {"a", "img", "div", "span"}
_ALLOWED_ATTRIBUTES = {"a": ["href"], "img": ["src", "alt"], "div": ["class"], "span": ["class"]}


def _date(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).isoformat()
    except ValueError as exc:
        raise HTTPException(400, "Invalid campaign date") from exc


async def _audit(action: str, banner_id: int | None = None):
    try:
        await log_event(
            "admin_action",
            status="ok",
            meta_json=json.dumps({"action": action, "banner_id": banner_id}),
        )
    except Exception:
        pass


@router.get("/admin/banners")
async def list_banners(_admin=Depends(require_admin)):
    async with await get_db() as db:
        cur = await db.execute(
            "SELECT id,title,image_url,target_url,alt_text,weight,active_from,active_to,enabled,position,html_snippet FROM banners ORDER BY id DESC"
        )
        rows = await cur.fetchall()
    return [dict(row) for row in rows]


@router.post("/admin/banners/upload")
async def upload_banner_image(image: UploadFile = File(...), _admin=Depends(require_admin)):
    data = await image.read(MAX_IMAGE_SIZE + 1)
    if len(data) > MAX_IMAGE_SIZE:
        raise HTTPException(413, "Image exceeds 2 MB")
    signature = next(
        ((ext, mime) for magic, (ext, mime) in MIMES.items() if data.startswith(magic)), None
    )
    if not signature:
        raise HTTPException(400, "Unsupported image")
    ext, mime = signature
    if ext == "webp" and data[8:12] != b"WEBP":
        raise HTTPException(400, "Invalid WebP image")
    BANNER_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.{ext}"
    (BANNER_DIR / filename).write_bytes(data)
    await _audit("banner_image_upload")
    return {"filename": filename, "url": f"/data/banners/{filename}", "content_type": mime}


@router.post("/admin/banners")
async def create_banner(
    title: str = Form(...),
    image_url: str = Form(...),
    target_url: str = Form(...),
    alt_text: str = Form(""),
    weight: int = Form(1),
    position: str = Form("bottom"),
    active_from: str = Form(""),
    active_to: str = Form(""),
    enabled: bool = Form(True),
    html_snippet: str = Form(""),
    _admin=Depends(require_admin),
):
    target = urlsplit(target_url)
    if position not in POSITIONS or weight < 0:
        raise HTTPException(400, "Invalid position or weight")
    if target.scheme not in {"https", "http"} or not target.netloc:
        raise HTTPException(400, "target_url must be a valid http(s) URL")
    if not re.fullmatch(r"/data/banners/[a-f0-9]{32}\.(png|jpg|gif|webp)", image_url):
        raise HTTPException(400, "Upload the banner image first")
    start, end = _date(active_from), _date(active_to)
    if start and end and start > end:
        raise HTTPException(400, "active_from must be before active_to")
    safe_snippet = bleach.clean(
        html_snippet[:4000],
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRIBUTES,
        protocols={"http", "https"},
        strip=True,
    )
    async with await get_db() as db:
        cur = await db.execute(
            "INSERT INTO banners(title,image_url,target_url,alt_text,weight,active_from,active_to,enabled,position,html_snippet) VALUES(?,?,?,?,?,?,?,?,?,?)",
            (
                title.strip()[:120],
                image_url,
                target_url,
                alt_text[:250],
                weight,
                start,
                end,
                int(enabled),
                position,
                safe_snippet,
            ),
        )
        await db.commit()
        banner_id = cur.lastrowid
    await _audit("banner_create", banner_id)
    return {"id": banner_id, "created": True}


@router.patch("/admin/banners/{banner_id}")
async def update_banner(
    banner_id: int,
    enabled: bool | None = Form(None),
    weight: int | None = Form(None),
    position: str | None = Form(None),
    active_from: str | None = Form(None),
    active_to: str | None = Form(None),
    _admin=Depends(require_admin),
):
    updates = {}
    if enabled is not None:
        updates["enabled"] = int(enabled)
    if weight is not None:
        if weight < 0:
            raise HTTPException(400, "weight must be >= 0")
        updates["weight"] = weight
    if position is not None:
        if position not in POSITIONS:
            raise HTTPException(400, "Invalid position")
        updates["position"] = position
    if active_from is not None:
        updates["active_from"] = _date(active_from)
    if active_to is not None:
        updates["active_to"] = _date(active_to)
    if not updates:
        raise HTTPException(400, "No fields to update")
    async with await get_db() as db:
        cur = await db.execute("SELECT active_from,active_to FROM banners WHERE id=?", (banner_id,))
        current = await cur.fetchone()
        if not current:
            raise HTTPException(404, "Banner not found")
        start = updates.get("active_from", current[0])
        end = updates.get("active_to", current[1])
        if start and end:
            cur = await db.execute("SELECT datetime(?) <= datetime(?)", (start, end))
            if not (await cur.fetchone())[0]:
                raise HTTPException(400, "active_from must be before active_to")
        sql = "UPDATE banners SET " + ",".join(f"{key}=?" for key in updates) + " WHERE id=?"
        await db.execute(sql, (*updates.values(), banner_id))
        await db.commit()
    await _audit("banner_update", banner_id)
    return {"updated": True}


@router.delete("/admin/banners/{banner_id}")
async def delete_banner(banner_id: int, _admin=Depends(require_admin)):
    async with await get_db() as db:
        cur = await db.execute("SELECT image_url FROM banners WHERE id=?", (banner_id,))
        row = await cur.fetchone()
        if not row:
            raise HTTPException(404, "Banner not found")
        image_url = row[0]
        await db.execute("DELETE FROM banners WHERE id=?", (banner_id,))
        await db.commit()
        cur = await db.execute("SELECT COUNT(*) FROM banners WHERE image_url=?", (image_url,))
        used = (await cur.fetchone())[0]
    if not used and image_url.startswith("/data/banners/"):
        try:
            (BANNER_DIR / image_url.rsplit("/", 1)[-1]).unlink()
        except FileNotFoundError:
            pass
    await _audit("banner_delete", banner_id)
    return {"deleted": True}
