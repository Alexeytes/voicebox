import aiosqlite
from app.config import settings
import os
DB_FILE = os.path.join("data","voicebox.db")
async def get_db():
    return await aiosqlite.connect(DB_FILE)
