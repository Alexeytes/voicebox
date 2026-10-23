from __future__ import annotations

from urllib.parse import urlsplit

import bleach
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse

from app.ads.service import select_active_banner
from app.db.database import get_db

router = APIRouter()
POSITIONS = {"top", "sidebar", "between", "bottom"}


@router.get("/ads")
async def ads(position: str = Query("top")):
    if position not in POSITIONS:
        raise HTTPException(400, "Unknown banner position")
    chosen = await select_active_banner(position)
    if not chosen:
        return []
    async with await get_db() as db:
        await db.execute(
            "INSERT INTO stats_events(event_type,status,meta_json) VALUES('banner_shown','ok',?)",
            (str(chosen.id),),
        )
        await db.commit()
    safe_snippet = bleach.clean(
        chosen.html_snippet or "",
        tags={"a", "img", "div", "span"},
        attributes={"a": ["href"], "img": ["src", "alt"], "div": ["class"], "span": ["class"]},
        protocols={"http", "https"},
        strip=True,
    )
    return [
        {
            "id": chosen.id,
            "title": chosen.title,
            "image_url": chosen.image_url,
            "alt_text": chosen.alt_text,
            "html_snippet": safe_snippet,
            "click_url": f"/go/banner/{chosen.id}",
        }
    ]


@router.get("/go/banner/{banner_id}")
async def banner_click(banner_id: int):
    async with await get_db() as db:
        cur = await db.execute(
            "SELECT target_url FROM banners WHERE id=? AND enabled=1", (banner_id,)
        )
        row = await cur.fetchone()
        if row:
            await db.execute(
                "INSERT INTO stats_events(event_type,status,meta_json) VALUES('banner_clicked','ok',?)",
                (str(banner_id),),
            )
            await db.commit()
    if not row:
        raise HTTPException(404, "Баннер не найден")
    destination = urlsplit(row[0])
    if destination.scheme not in {"http", "https"} or not destination.netloc:
        raise HTTPException(404, "Баннер не найден")
    return RedirectResponse(row[0], status_code=302)
