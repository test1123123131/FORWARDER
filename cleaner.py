import re
from typing import Optional
from telethon import TelegramClient
from telethon.tl.types import Message


# Patterns to remove from message text
_CHANNEL_PATTERN = re.compile(r"@[\w]{5,}")
_LINK_PATTERN = re.compile(
    r"(?:https?://)?(?:t\.me|telegram\.me)/(?:joinchat/[\w-]+|[\w]+)",
    re.IGNORECASE,
)
_INVITE_LINK_PATTERN = re.compile(r"t\.me/\+[\w-]+")
_FOOTER_PATTERNS = [
    re.compile(r"[-=]{3,}\s*канал.*$", re.IGNORECASE),  # Russian channel footer
    re.compile(r"[-=]{3,}\s*کانال.*$", re.IGNORECASE),  # Persian channel footer
    re.compile(r"[-=]{3,}\s*channel.*$", re.IGNORECASE),  # English channel footer
    re.compile(r" канал\s+@\w+", re.IGNORECASE),
    re.compile(r" کانال\s+@\w+", re.IGNORECASE),
    re.compile(r" channel\s+@\w+", re.IGNORECASE),
]


def clean_text(text: str, source_username: Optional[str] = None) -> str:
    if not text:
        return text

    cleaned = text

    # Remove @mentions of channels
    cleaned = _CHANNEL_PATTERN.sub("", cleaned)

    # Remove t.me links (invite links and channel links)
    cleaned = _INVITE_LINK_PATTERN.sub("", cleaned)
    cleaned = _LINK_PATTERN.sub("", cleaned)

    # Remove known footer patterns
    for pattern in _FOOTER_PATTERNS:
        cleaned = pattern.sub("", cleaned)

    # If we know the source username, remove any remaining reference
    if source_username:
        username_clean = source_username.lstrip("@")
        cleaned = re.sub(
            re.escape(username_clean), "", cleaned, flags=re.IGNORECASE
        )

    # Clean up excessive whitespace / empty lines
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = cleaned.strip()

    return cleaned


async def forward_message(
    client: TelegramClient,
    source_chat,
    message: Message,
    dest_chat,
    strip_watermark: bool = True,
) -> bool:
    """Forward a message to destination, stripping channel identity if requested."""
    try:
        text = message.text or message.message or ""
        source_username = None

        # Get source username for cleanup
        try:
            source_entity = await client.get_entity(source_chat)
            source_username = getattr(source_entity, "username", None)
        except Exception:
            pass

        cleaned_text = clean_text(text, source_username) if strip_watermark else text

        # If message has media, send it with the cleaned caption
        if message.media:
            await client.send_file(
                dest_chat,
                file=message.media,
                caption=cleaned_text or None,
                force_document=False,
                voice_note=message.voice_note if hasattr(message, "voice_note") else False,
                video_note=message.video_note if hasattr(message, "video_note") else False,
                round_message=message.round if hasattr(message, "round") else False,
                supports_streaming=True,
                progress_callback=None,
            )
            return True

        # Text-only message
        if cleaned_text:
            await client.send_message(dest_chat, cleaned_text)
            return True

        # Message has neither media nor text after cleaning — skip
        return False

    except Exception as e:
        print(f"[FORWARD ERROR] Message {message.id}: {e}")
        return False
