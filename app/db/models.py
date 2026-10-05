from dataclasses import dataclass
from datetime import datetime
from typing import Optional

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
    lang: Optional[str]
    voice_id: Optional[str]
    engine: Optional[str]
    duration_ms: Optional[int]
    status: Optional[str]
    meta_json: Optional[str]

@dataclass()
class Banner:
    id: int
    title: str
    image_url: str
    target_url: str
    alt_text: str
    weight: int
    active_from: Optional[datetime]
    active_to: Optional[datetime]
    enabled: bool
    position: str
    html_snippet: Optional[str]
