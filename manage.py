"""
Channel management utility.
Usage:
    python manage.py list              - Show current channels
    python manage.py add @channel      - Add a source channel
    python manage.py remove @channel   - Remove a source channel
    python manage.py dest @channel     - Change destination channel
"""

import sys
import os
from dotenv import load_dotenv, set_key

ENV_FILE = os.path.join(os.path.dirname(__file__), ".env")

load_dotenv(ENV_FILE)


def get_source_list():
    raw = os.getenv("SOURCE_CHANNELS", "")
    if not raw.strip():
        return []
    return [ch.strip() for ch in raw.split(",") if ch.strip()]


def show_channels():
    sources = get_source_list()
    dest = os.getenv("DEST_CHANNEL", "(not set)")

    print("\n=== Current Configuration ===")
    print(f"\nDestination Channel: {dest}")
    print(f"\nSource Channels ({len(sources)}):")
    for i, ch in enumerate(sources, 1):
        print(f"  {i}. {ch}")

    if not sources:
        print("  (none)")
    print()


def add_source(channel: str):
    sources = get_source_list()
    if channel in sources:
        print(f"'{channel}' is already in source list.")
        return
    sources.append(channel)
    set_key(ENV_FILE, "SOURCE_CHANNELS", ",".join(sources))
    print(f"Added '{channel}'. Sources: {len(sources)}")


def remove_source(channel: str):
    sources = get_source_list()
    if channel not in sources:
        print(f"'{channel}' not found in source list.")
        return
    sources.remove(channel)
    set_key(ENV_FILE, "SOURCE_CHANNELS", ",".join(sources))
    print(f"Removed '{channel}'. Sources: {len(sources)}")


def change_dest(channel: str):
    set_key(ENV_FILE, "DEST_CHANNEL", channel)
    print(f"Destination changed to '{channel}'")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1].lower()

    if cmd == "list":
        show_channels()
    elif cmd == "add" and len(sys.argv) >= 3:
        add_source(sys.argv[2])
    elif cmd == "remove" and len(sys.argv) >= 3:
        remove_source(sys.argv[2])
    elif cmd == "dest" and len(sys.argv) >= 3:
        change_dest(sys.argv[2])
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
