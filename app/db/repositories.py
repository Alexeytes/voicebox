from app.db.database import get_db
from app.db.models import User, StatsEvent, Banner
from dataclasses import asdict
import aiosqlite
from typing import Optional, List

async def get_user_by_username(username: str) -> Optional[User]:
    db = await get_db()
    row = await db.execute_fetchone("SELECT * FROM users WHERE username = ?", (username,))
    await db.close()
    if not row:
        return None
    return User(**dict(zip([c[0] for c in db.description], row)))

async def add_stats_event(event: StatsEvent) -> int:
    db = await get_db()
    data = asdict(event)
    cols = [k for k in data.keys() if data[k] is not None]
    values = [data[k] for k in cols]
    placeholders = ','.join(['?']*len(values))
    sql = f"INSERT INTO stats_events ({','.join(cols)}) VALUES ({placeholders})"
    cur = await db.execute(sql, values)
    await db.commit()
    await db.close()
    return cur.lastrowid
