import sys
import getpass
import asyncio
from app.db.database import get_db
from app.auth.passwords import hash_password
from app.config import settings

async def create_user(username: str):
    db = await get_db()
    password = getpass.getpass(f"Set password for {username}: ")
    h = hash_password(password)
    await db.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, h))
    await db.commit()
    await db.close()
    print("User created.")

def main():
    if len(sys.argv) < 3:
        print("Usage: python -m app.admin cli create-user <username>")
        sys.exit(1)
    cmd, username = sys.argv[1], sys.argv[2]
    if cmd == "create-user":
        asyncio.run(create_user(username))
    else:
        print("Unknown command")

if __name__ == "__main__":
    main()
