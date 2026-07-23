import asyncio
import logging
import sys
from telethon import TelegramClient, events
from telethon.tl.types import PeerChannel, PeerUser

from config import Config
from cleaner import forward_message

logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("forwarder")


async def main():
    if not Config.validate():
        logger.error("Invalid configuration. Please check your .env file.")
        sys.exit(1)

    client = TelegramClient("forwarder_session", Config.API_ID, Config.API_HASH)
    await client.start(phone=Config.PHONE)

    me = await client.get_me()
    logger.info(f"Logged in as: {me.first_name} (@{me.username})")

    # Resolve source channels
    source_ids = set()
    source_map = {}
    for ch in Config.get_source_channels():
        try:
            entity = await client.get_entity(ch)
            source_ids.add(entity.id)
            source_map[entity.id] = ch
            logger.info(f"Monitoring source: {ch} (ID: {entity.id})")
        except Exception as e:
            logger.error(f"Cannot resolve source channel '{ch}': {e}")

    if not source_ids:
        logger.error("No valid source channels found.")
        sys.exit(1)

    # Resolve destination channel
    try:
        dest_entity = await client.get_entity(Config.DEST_CHANNEL)
        logger.info(f"Destination: {Config.DEST_CHANNEL} (ID: {dest_entity.id})")
    except Exception as e:
        logger.error(f"Cannot resolve destination channel '{Config.DEST_CHANNEL}': {e}")
        sys.exit(1)

    # Counter
    forwarded_count = 0

    @client.on(events.NewMessage(chats=list(source_ids)))
    async def handler(event):
        nonlocal forwarded_count

        msg = event.message
        source = source_map.get(event.chat_id, str(event.chat_id))

        # Skip empty messages (no text and no media)
        if not msg.text and not msg.message and not msg.media:
            logger.debug(f"Skipping empty message from {source}")
            return

        logger.info(f"New message from {source} (ID: {msg.id})")

        success = await forward_message(
            client=client,
            source_chat=event.chat_id,
            message=msg,
            dest_chat=dest_entity.id,
            strip_watermark=True,
        )

        if success:
            forwarded_count += 1
            logger.info(
                f"Forwarded #{forwarded_count} from {source} -> {Config.DEST_CHANNEL}"
            )
        else:
            logger.warning(f"Failed or skipped message from {source}")

        # Small delay to avoid flood waits
        if Config.FORWARD_DELAY > 0:
            await asyncio.sleep(Config.FORWARD_DELAY)

    logger.info("=" * 50)
    logger.info("Bot is running. Press Ctrl+C to stop.")
    logger.info(f"Monitoring {len(source_ids)} source(s)")
    logger.info("=" * 50)

    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
