from __future__ import annotations

from datetime import datetime

from app.db.database import get_db
from app.db.models import Banner, StatsEvent, User


async def get_user_by_username(username: str) -> User | None:
    async with await get_db() as db:
        cursor = await db.execute(
            "SELECT id, username, password_hash, created_at FROM users WHERE username = ?",
            (username,),
        )
        row = await cursor.fetchone()
    return User(row[0], row[1], row[2], datetime.fromisoformat(row[3])) if row else None


async def get_user_by_id(user_id: int) -> User | None:
    async with await get_db() as db:
        cursor = await db.execute(
            "SELECT id, username, password_hash, created_at FROM users WHERE id = ?", (user_id,)
        )
        row = await cursor.fetchone()
    return User(row[0], row[1], row[2], datetime.fromisoformat(row[3])) if row else None


async def add_stats_event(event: StatsEvent) -> int:
    async with await get_db() as db:
        cursor = await db.execute(
            "INSERT INTO stats_events (event_type, ip_hash, lang, voice_id, engine, duration_ms, status, meta_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                event.event_type,
                event.ip_hash,
                event.lang,
                event.voice_id,
                event.engine,
                event.duration_ms,
                event.status,
                event.meta_json,
            ),
        )
        await db.commit()
        return cursor.lastrowid or 0


async def get_active_banners(position: str, now: datetime | None = None) -> list[Banner]:
    now = now or datetime.utcnow()
    async with await get_db() as db:
        cursor = await db.execute(
            "SELECT id,title,image_url,target_url,alt_text,weight,active_from,active_to,enabled,position,html_snippet FROM banners WHERE enabled=1 AND position=? AND (active_from IS NULL OR datetime(active_from)<=datetime(?)) AND (active_to IS NULL OR datetime(active_to)>=datetime(?)) ORDER BY id DESC",
            (position, now.isoformat(), now.isoformat()),
        )
        rows = await cursor.fetchall()
    return [
        Banner(
            row[0],
            row[1],
            row[2] or "",
            row[3] or "",
            row[4] or "",
            row[5] or 1,
            datetime.fromisoformat(row[6]) if row[6] else None,
            datetime.fromisoformat(row[7]) if row[7] else None,
            bool(row[8]),
            row[9] or "bottom",
            row[10],
        )
        for row in rows
    ]


async def read_app_settings() -> dict[str, str]:
    async with await get_db() as db:
        cur = await db.execute("SELECT key,value FROM app_settings")
        return {row[0]: row[1] for row in await cur.fetchall()}


async def write_app_settings(values: dict[str, str]) -> None:
    async with await get_db() as db:
        await db.executemany(
            "INSERT INTO app_settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            values.items(),
        )
        await db.commit()
