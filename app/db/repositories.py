from dataclasses import asdict

from app.db.database import get_db
from app.db.models import StatsEvent, User


async def get_user_by_username(username: str) -> User | None:
    db = await get_db()
    row = await db.execute_fetchone("SELECT * FROM users WHERE username = ?", (username,))
    await db.close()
    if not row:
        return None
    return User(**dict(zip([c[0] for c in db.description], row, strict=False)))

async def add_stats_event(event: StatsEvent) -> int:
    db = await get_db()
    data = asdict(event)
    cols = [k for k in data if data[k] is not None]
    values = [data[k] for k in cols]
    placeholders = ','.join(['?']*len(values))
    sql = f"INSERT INTO stats_events ({','.join(cols)}) VALUES ({placeholders})"
    cur = await db.execute(sql, values)
    await db.commit()
    await db.close()
    return cur.lastrowid
