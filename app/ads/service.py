from __future__ import annotations

import random
from datetime import datetime

from app.db.models import Banner
from app.db.repositories import get_active_banners


async def select_active_banner(position: str, now: datetime | None = None) -> Banner | None:
    banners = await get_active_banners(position, now)
    if not banners:
        return None
    weights = [max(0, banner.weight) for banner in banners]
    if sum(weights) == 0:
        return random.choice(banners)
    return random.choices(banners, weights=weights, k=1)[0]
