from datetime import datetime

from app.db.models import StatsEvent
from app.db.repositories import add_stats_event


async def log_event(event_type: str, **data):
    event = StatsEvent(
        id=0,
        ts=datetime.utcnow(),
        event_type=event_type,
        ip_hash=data.get("ip_hash"),
        lang=data.get("lang"),
        voice_id=data.get("voice_id"),
        engine=data.get("engine"),
        duration_ms=data.get("duration_ms"),
        status=data.get("status"),
        meta_json=data.get("meta_json"),
    )
    await add_stats_event(event)
