import re
import logging
from datetime import datetime, timezone

from pyrogram.types import Message


def setup_logger(level: str = "INFO") -> logging.Logger:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return logging.getLogger("forwarder")


def clean_forwarded_message(message: Message) -> dict:
    """
    Extract media and text from a message, stripping forwarded-from
    attributions, source-channel watermarks, and ad-like patterns.
    Returns a dict of kwargs suitable for client.send_message / send_media.
    """
    text = message.text or message.caption or ""
    entities = message.entities or message.caption_entities or []

    # ── Strip "Forwarded from …" header ──────────────────────────────
    text = re.sub(r"Forwarded from .+\n*", "", text, flags=re.IGNORECASE)

    # ── Strip common ad / watermark patterns ──────────────────────────
    ad_patterns = [
        r"@[\w]+",                                    # @usernames
        r"https?://t\.me/[\w]+",                      # t.me links
        r"Join @[\w]+",                               # join prompts
        r"Subscribe @[\w]+",                           # subscribe prompts
        r"📢\s*@[\w]+",                               # 📢 @channel
        r"🔗\s*https?://\S+",                         # link lines
        r"Source:\s*\S+",                             # source attributions
        r"━━━━━━━━━━━━━━━━",                           # separator lines
        r"╚+═+╝",                                     # box borders
        r"[★☆]{3,}",                                  # star separators
    ]
    for pat in ad_patterns:
        text = re.sub(pat, "", text, flags=re.IGNORECASE)

    # Collapse multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text).strip()

    return {
        "text": text,
        "entities": entities,
    }


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
