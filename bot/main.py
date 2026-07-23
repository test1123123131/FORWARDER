import asyncio
import logging
import sys
import os

from pyrogram import Client, filters

from bot.config import Config
from bot.database import Database
from bot.forwarder import Forwarder
from bot.handlers import register_handlers
from bot.utils import setup_logger

logger = logging.getLogger(__name__)


def build_app() -> Client:
    """Create and configure the Pyrogram client."""
    return Client(
        name=Config.SESSION_NAME,
        api_id=Config.API_ID,
        api_hash=Config.API_HASH,
        workdir=Config.DATA_DIR,
    )


async def main():
    # ── Setup ────────────────────────────────────────────────────────
    setup_logger(Config.LOG_LEVEL)
    Config.validate()

    db = Database()
    app = build_app()
    forwarder = Forwarder(app, db)

    # ── Register handlers ────────────────────────────────────────────
    register_handlers(app, db)

    # Register the core forwarding handler (catch-all for new messages)
    @app.on_message(filters.new_chat_messages & ~filters.private)
    async def _forward_handler(client, message):
        await forwarder.on_message(client, message)

    # ── Start ────────────────────────────────────────────────────────
    logger.info("Starting Telegram Forwarder Bot...")
    await app.start()
    logger.info("Pyrogram client started")

    me = await app.get_me()
    logger.info("Logged in as: %s (ID: %d)", me.first_name, me.id)

    await forwarder.start()

    # Notify owner
    if Config.OWNER_ID:
        try:
            await app.send_message(
                Config.OWNER_ID,
                "🚀 **Forwarder Bot Started**\n\n"
                f"  👤 Account: `{me.first_name}`\n"
                f"  📡 Sources: `{db.get_source_count()}`\n"
                f"  🎯 Target: `{db.get_target_channel()}`\n"
                f"  ⚡ Status: `{'ON' if db.is_enabled() else 'OFF'}`\n\n"
                "Send /panel to manage.",
            )
        except Exception as e:
            logger.warning("Could not notify owner: %s", e)

    # ── Keep alive ───────────────────────────────────────────────────
    logger.info("Bot is running. Press Ctrl+C to stop.")
    try:
        await asyncio.Event().wait()  # Block forever
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        await forwarder.stop()
        await app.stop()
        logger.info("Bot stopped.")


if __name__ == "__main__":
    from pyrogram import idle  # noqa: keep import for fallback

    loop = asyncio.get_event_loop_policy().new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()
