from __future__ import annotations

import logging
import re
from pathlib import Path

import aiosqlite

from app.config import settings

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
DB_FILE = DATA_DIR / "voicebox.db"
MIGRATION = Path(__file__).resolve().parent / "migrations" / "0001_init.sql"


class _DatabaseConnection:
    def __init__(self, path: Path):
        self.path = path
        self.connection: aiosqlite.Connection | None = None

    async def __aenter__(self) -> aiosqlite.Connection:
        self.connection = await aiosqlite.connect(self.path)
        self.connection.row_factory = aiosqlite.Row
        return self.connection

    async def __aexit__(self, exc_type, exc, traceback) -> None:
        if self.connection is not None:
            await self.connection.close()


async def get_db() -> _DatabaseConnection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return _DatabaseConnection(DB_FILE)


async def initialize_database() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_FILE) as db:
        await db.executescript(MIGRATION.read_text(encoding="utf-8"))
        await db.commit()
        cursor = await db.execute("SELECT COUNT(*) FROM users")
        user_count = (await cursor.fetchone())[0]
        if user_count == 0:
            password = settings.ADMIN_PASSWORD
            unsafe = len(password) < 12 or re.search(
                r"change|example|replace|your|default|password|xxxx", password, re.I
            )
            if unsafe:
                logger.warning(
                    "Initial administrator not created: configure a non-placeholder ADMIN_PASSWORD (12+ characters), then run python -m app.admin bootstrap."
                )
            else:
                from app.auth.passwords import hash_password

                await db.execute(
                    "INSERT INTO users(username,password_hash) VALUES(?,?)",
                    (settings.ADMIN_USERNAME, hash_password(password)),
                )
                await db.commit()
                logger.info("Created the initial administrator account from environment settings")
