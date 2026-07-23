"""
Generate a StringSession for Pyrogram.
Run this ONCE on your local machine, then copy the output to Railway as
the SESSION_STRING environment variable.

Usage:
    pip install -r requirements.txt
    python generate_session.py
"""
import asyncio
from pyrogram import Client
from pyrogram.session import StringSession

API_ID = int(input("Enter API_ID: "))
API_HASH = input("Enter API_HASH: ")

app = Client(
    name="temp_session",
    api_id=API_ID,
    api_hash=API_HASH,
    in_memory=True,
)

async def main():
    await app.start()
    session_string = StringSession.export(await app.storage.export())
    print("\n" + "=" * 60)
    print("YOUR SESSION STRING (copy this to Railway):\n")
    print(session_string)
    print("\n" + "=" * 60)
    await app.stop()

with app:
    asyncio.run(main())
