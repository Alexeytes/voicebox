import random, time
from app.db.repositories import get_active_banners

def select_active_banner(position: str, now: float = None):
    banners = get_active_banners(position, now or time.time())
    if not banners:
        return None
    total_weight = sum(b.weight for b in banners)
    if total_weight == 0:
        return random.choice(banners)
    pick = random.uniform(0, total_weight)
    s = 0
    for b in banners:
        s += b.weight
        if pick <= s:
            return b
    return banners[-1]
