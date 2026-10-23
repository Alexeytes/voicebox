from __future__ import annotations

import asyncio
import csv
import getpass
import re
import sys
from pathlib import Path

from app.auth.passwords import hash_password
from app.config import settings
from app.db.database import get_db, initialize_database


def validate_password(password: str) -> None:
    if len(password) < 12 or any(
        marker in password.lower()
        for marker in ("change", "example", "replace", "your", "default", "password", "xxxx")
    ):
        raise ValueError("Use a non-placeholder password of at least 12 characters")


async def create_user(username: str, password: str | None = None):
    password = password or getpass.getpass(f"Set password for {username}: ")
    validate_password(password)
    async with await get_db() as db:
        await db.execute(
            "INSERT INTO users(username,password_hash) VALUES(?,?)",
            (username, hash_password(password)),
        )
        await db.commit()
    print(f"Administrator {username} created.")


async def reset_password(username: str):
    password = getpass.getpass(f"New password for {username}: ")
    validate_password(password)
    async with await get_db() as db:
        cur = await db.execute(
            "UPDATE users SET password_hash=? WHERE username=?", (hash_password(password), username)
        )
        await db.commit()
        if cur.rowcount == 0:
            raise ValueError("User not found")
    print(f"Password updated for {username}.")


async def bootstrap():
    async with await get_db() as db:
        cur = await db.execute("SELECT 1 FROM users LIMIT 1")
        exists = await cur.fetchone()
    if exists:
        raise SystemExit(
            "An administrator already exists; use create-user for an additional account."
        )
    await create_user(settings.ADMIN_USERNAME, settings.ADMIN_PASSWORD)


async def list_users():
    async with await get_db() as db:
        cur = await db.execute("SELECT username,created_at FROM users ORDER BY username")
        rows = await cur.fetchall()
    for row in rows:
        print(f"{row[0]}\t{row[1]}")


async def prune_stats(age: str):
    match = re.fullmatch(r"(\d+)d", age)
    if not match or int(match.group(1)) < 1:
        raise ValueError("Use --older-than such as 90d")
    async with await get_db() as db:
        cur = await db.execute(
            "DELETE FROM stats_events WHERE datetime(ts) < datetime('now',?)",
            (f"-{match.group(1)} days",),
        )
        await db.commit()
        removed = cur.rowcount
    print(f"Removed {removed} events.")


async def export_stats(output: str):
    async with await get_db() as db:
        cur = await db.execute(
            "SELECT ts,event_type,ip_hash,lang,voice_id,engine,duration_ms,status,meta_json FROM stats_events ORDER BY id"
        )
        rows = await cur.fetchall()
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
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
    print(f"Exported {len(rows)} events to {path}.")


async def _run(command):
    await initialize_database()
    await command


def main():
    args = sys.argv[1:]
    if args == ["bootstrap"]:
        command = bootstrap()
    elif len(args) == 2 and args[0] == "create-user":
        command = create_user(args[1])
    elif len(args) == 2 and args[0] == "reset-password":
        command = reset_password(args[1])
    elif args == ["list-users"]:
        command = list_users()
    elif len(args) == 3 and args[0] == "prune-stats" and args[1] == "--older-than":
        command = prune_stats(args[2])
    elif len(args) == 2 and args[0] == "export-stats":
        command = export_stats(args[1])
    else:
        print(
            "Usage: python -m app.admin {bootstrap|create-user USER|reset-password USER|list-users|prune-stats --older-than 90d|export-stats PATH.csv}"
        )
        sys.exit(2)
    asyncio.run(_run(command))


if __name__ == "__main__":
    main()
