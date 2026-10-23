from __future__ import annotations

import csv
import io

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse, StreamingResponse

from app.auth.sessions import require_admin
from app.db.database import get_db

router = APIRouter()
_PERIODS = {"24h": "-1 day", "7d": "-7 days", "30d": "-30 days"}


@router.get("/admin/stats", response_class=HTMLResponse)
def stats_page(_admin=Depends(require_admin)):
    return HTMLResponse(
        """<!doctype html><html lang='ru'><meta charset='utf-8'><meta name='viewport' content='width=device-width'><title>Статистика · Voice Box</title><body style='font:15px system-ui;background:#101720;color:#eef;padding:28px;max-width:1100px;margin:auto'><a style='color:#9be5c1' href='/admin/'>← Панель</a><h1>Статистика</h1><nav><button data-period='24h'>24 часа</button><button data-period='7d'>7 дней</button><button data-period='30d'>30 дней</button></nav><div id='cards'></div><svg id='chart' viewBox='0 0 800 180' role='img' aria-label='Синтезы по дням' style='width:100%;max-height:220px;background:#141c27;border-radius:12px'></svg><p><a style='color:#9be5c1' href='/admin/api/stats/export.csv'>Скачать CSV</a></p><h2>Журнал событий</h2><label>Тип события <select id='event-filter'><option value=''>Все</option><option>synthesis_requested</option><option>synthesis_done</option><option>synthesis_error</option><option>preview_done</option><option>banner_shown</option><option>banner_clicked</option><option>login_failed</option><option>admin_action</option></select></label><button id='events-prev'>Назад</button><button id='events-next'>Дальше</button><table style='width:100%;text-align:left'><thead><tr><th>Время UTC</th><th>Событие</th><th>Язык</th><th>Голос</th><th>Статус</th></tr></thead><tbody id='events'></tbody></table><script src='/static/stats.js' defer></script></body></html>"""
    )


@router.get("/admin/api/stats/overview")
async def overview(period: str = Query("7d"), _admin=Depends(require_admin)):
    if period not in _PERIODS:
        raise HTTPException(400, "period must be 24h, 7d or 30d")
    async with await get_db() as db:
        totals = {}
        for key, delta in _PERIODS.items():
            cur = await db.execute(
                "SELECT event_type,COUNT(*) FROM stats_events WHERE datetime(ts) >= datetime('now',?) GROUP BY event_type",
                (delta,),
            )
            totals[key] = {row[0]: row[1] for row in await cur.fetchall()}
        cur = await db.execute(
            "SELECT COUNT(*),AVG(duration_ms) FROM stats_events WHERE event_type='synthesis_done' AND datetime(ts) >= datetime('now',?)",
            (_PERIODS[period],),
        )
        done, avg_ms = await cur.fetchone()
        cur = await db.execute(
            "SELECT COUNT(*) FROM stats_events WHERE event_type='synthesis_error' AND ts >= datetime('now',?)",
            (_PERIODS[period],),
        )
        errors = (await cur.fetchone())[0]
        cur = await db.execute("SELECT COUNT(*) FROM banners WHERE enabled=1")
        banners = (await cur.fetchone())[0]
        cur = await db.execute(
            "SELECT SUM(event_type='banner_shown'),SUM(event_type='banner_clicked') FROM stats_events WHERE ts >= datetime('now',?)",
            (_PERIODS[period],),
        )
        impressions, clicks = await cur.fetchone()
    return {
        "period": period,
        "events_by_type": totals,
        "synthesis_done": done or 0,
        "synthesis_errors": errors or 0,
        "average_duration_ms": round(avg_ms or 0),
        "banner_impressions": impressions or 0,
        "banner_clicks": clicks or 0,
        "banner_ctr_percent": round(clicks * 100 / impressions, 2) if impressions else 0,
        "active_banners": banners,
    }


@router.get("/admin/api/stats/timeseries")
async def timeseries(
    metric: str = Query("synthesis"), range: str = Query("7d"), _admin=Depends(require_admin)
):
    if range not in _PERIODS or metric not in {"synthesis", "preview", "banner"}:
        raise HTTPException(400, "Invalid metric or range")
    event_filter = {
        "synthesis": "event_type IN ('synthesis_done','synthesis_error')",
        "preview": "event_type IN ('preview_done','preview_error')",
        "banner": "event_type IN ('banner_shown','banner_clicked')",
    }[metric]
    async with await get_db() as db:
        cur = await db.execute(
            f"SELECT strftime('%Y-%m-%d',ts) AS day,COUNT(*) FROM stats_events WHERE {event_filter} AND ts >= datetime('now',?) GROUP BY day ORDER BY day",
            (_PERIODS[range],),
        )
        return [{"date": row[0], "count": row[1]} for row in await cur.fetchall()]


@router.get("/admin/api/stats/events")
async def events(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    event_type: str | None = Query(None),
    _admin=Depends(require_admin),
):
    async with await get_db() as db:
        if event_type:
            cur = await db.execute(
                "SELECT ts,event_type,ip_hash,lang,voice_id,engine,duration_ms,status,meta_json FROM stats_events WHERE event_type=? ORDER BY id DESC LIMIT ? OFFSET ?",
                (event_type, limit, offset),
            )
        else:
            cur = await db.execute(
                "SELECT ts,event_type,ip_hash,lang,voice_id,engine,duration_ms,status,meta_json FROM stats_events ORDER BY id DESC LIMIT ? OFFSET ?",
                (limit, offset),
            )
        rows = await cur.fetchall()
    return {"items": [dict(row) for row in rows], "limit": limit, "offset": offset}


@router.get("/admin/api/stats/export.csv")
async def export_csv(_admin=Depends(require_admin)):
    async with await get_db() as db:
        cur = await db.execute(
            "SELECT ts,event_type,ip_hash,lang,voice_id,engine,duration_ms,status,meta_json FROM stats_events ORDER BY id"
        )
        rows = await cur.fetchall()
    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(
        [
            "ts",
            "event_type",
            "ip_hash",
            "lang",
            "voice_id",
            "engine",
            "duration_ms",
            "status",
            "meta_json",
        ]
    )
    writer.writerows([tuple(row) for row in rows])
    stream.seek(0)
    return StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=voicebox-stats.csv"},
    )
