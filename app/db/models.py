from dataclasses import dataclass
from datetime import datetime


@dataclass()
class User:
    id: int
    username: str
    password_hash: str
    created_at: datetime

@dataclass()
class StatsEvent:
    id: int
    ts: datetime
    event_type: str
    ip_hash: str
    lang: str | None
    voice_id: str | None
    engine: str | None
    duration_ms: int | None
    status: str | None
    meta_json: str | None

@dataclass()
class Banner:
    id: int
    title: str
    image_url: str
    target_url: str
    alt_text: str
    weight: int
    active_from: datetime | None
    active_to: datetime | None
    enabled: bool
    position: str
    html_snippet: str | None
