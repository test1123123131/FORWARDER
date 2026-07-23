import asyncio
import logging
from typing import Optional

from pyrogram import Client
from pyrogram.types import Message
from pyrogram.enums import ChatType

from bot.database import Database
from bot.utils import clean_forwarded_message

logger = logging.getLogger(__name__)


class Forwarder:
    """
    Monitors source channels and forwards new posts to the target channel.
    Handles: text, photos, videos, documents, audio, voice, animations,
    stickers, video notes, and media groups (albums).
    """

    def __init__(self, client: Client, db: Database):
        self.client = client
        self.db = db
        self._running = False
        # Track media groups: group_id -> [messages]
        self._media_groups: dict[int, list[Message]] = {}
        # Track which group_ids we've already dispatched
        self._dispatched_groups: set[int] = set()

    async def start(self):
        """Start listening on all source channels."""
        if self._running:
            return
        self._running = True

        # Register handler for new messages on all source channels
        for source in self.db.get_sources():
            await self._add_channel_listener(source["id"])

        logger.info("Forwarder started — monitoring %d source(s)", self.db.get_source_count())

    async def stop(self):
        self._running = False
        logger.info("Forwarder stopped")

    async def refresh_sources(self):
        """Re-sync listeners after source list changes."""
        # Pyrogram doesn't expose a clean way to remove per-chat filters,
        # so we rely on the handler checking db.is_enabled() + db.get_source_ids().
        # This is a no-op for now — the filter in _handle_message does the gating.
        logger.info("Sources refreshed (listener check is live)")

    async def _add_channel_listener(self, channel_id: int):
        """
        We use a single catch-all handler registered once in main.py.
        This method exists as a hook if per-channel setup is ever needed.
        """
        pass

    # ── Core message handler (registered once in main.py) ─────────────

    async def on_message(self, client: Client, message: Message):
        """
        Called for every new message in any chat the userbot is in.
        We filter to only source channels here.
        """
        if not self._running:
            return
        if not self.db.is_enabled():
            return
        if message.chat is None:
            return
        if message.chat.id not in self.db.get_source_ids():
            return
        # Skip messages from the target channel to avoid loops
        target = self.db.get_target_channel()
        try:
            target_chat = await client.get_chat(target)
            if message.chat.id == target_chat.id:
                return
        except Exception:
            pass

        # ── Media group (album) handling ─────────────────────────────
        if message.media_group_id:
            await self._handle_media_group(message)
            return

        # ── Single message forwarding ────────────────────────────────
        await self._forward_single(message)

    async def _handle_media_group(self, message: Message):
        """Collect album messages, then forward the full album once."""
        gid = message.media_group_id
        if gid in self._dispatched_groups:
            return

        # Collect messages for this group
        if gid not in self._media_groups:
            self._media_groups[gid] = []
        self._media_groups[gid].append(message)

        # Wait briefly for other album messages to arrive
        await asyncio.sleep(1.5)

        # Check again — another handler instance may have dispatched
        if gid in self._dispatched_groups:
            self._media_groups.pop(gid, None)
            return

        self._dispatched_groups.add(gid)
        messages = self._media_groups.pop(gid, [])

        if not messages:
            return

        # Sort by message_id to preserve order
        messages.sort(key=lambda m: m.id)

        # Build the album for the target
        target = self.db.get_target_channel()
        caption_data = clean_forwarded_message(messages[0])
        caption = caption_data["text"]
        caption_entities = caption_data["entities"]

        media_list = []
        for msg in messages:
            if msg.photo:
                media_list.append(("photo", msg.photo.file_id))
            elif msg.video:
                media_list.append(("video", msg.video.file_id))
            elif msg.document:
                media_list.append(("document", msg.document.file_id))
            elif msg.audio:
                media_list.append(("audio", msg.audio.file_id))
            elif msg.voice:
                media_list.append(("voice", msg.voice.file_id))
            elif msg.animation:
                media_list.append(("animation", msg.animation.file_id))
            elif msg.sticker:
                media_list.append(("sticker", msg.sticker.file_id))

        if not media_list:
            return

        try:
            # Use send_media_group for albums
            from pyrogram.types import InputMediaPhoto, InputMediaVideo, InputMediaDocument, InputMediaAudio

            media_group = []
            for i, (media_type, file_id) in enumerate(media_list):
                caption_text = caption if i == 0 else None
                caption_ents = caption_entities if i == 0 else None
                if media_type == "photo":
                    media_group.append(InputMediaPhoto(
                        media=file_id,
                        caption=caption_text,
                        caption_entities=caption_ents,
                    ))
                elif media_type == "video":
                    media_group.append(InputMediaVideo(
                        media=file_id,
                        caption=caption_text,
                        caption_entities=caption_ents,
                    ))
                elif media_type == "document":
                    media_group.append(InputMediaDocument(
                        media=file_id,
                        caption=caption_text,
                        caption_entities=caption_ents,
                    ))
                elif media_type == "audio":
                    media_group.append(InputMediaAudio(
                        media=file_id,
                        caption=caption_text,
                        caption_entities=caption_ents,
                    ))

            if media_group:
                await self.client.send_media_group(target, media=media_group)
                logger.info("Forwarded album (%d items) to %s", len(media_group), target)
        except Exception as e:
            logger.error("Failed to forward album: %s", e)

    async def _forward_single(self, message: Message):
        """Forward a single message, stripping forwarded-from headers."""
        target = self.db.get_target_channel()
        try:
            cleaned = clean_forwarded_message(message)

            if message.photo:
                await self.client.send_photo(
                    target,
                    photo=message.photo.file_id,
                    caption=cleaned["text"],
                    caption_entities=cleaned["entities"],
                )
            elif message.video:
                await self.client.send_video(
                    target,
                    video=message.video.file_id,
                    caption=cleaned["text"],
                    caption_entities=cleaned["entities"],
                )
            elif message.document:
                await self.client.send_document(
                    target,
                    document=message.document.file_id,
                    caption=cleaned["text"],
                    caption_entities=cleaned["entities"],
                )
            elif message.audio:
                await self.client.send_audio(
                    target,
                    audio=message.audio.file_id,
                    caption=cleaned["text"],
                    caption_entities=cleaned["entities"],
                )
            elif message.voice:
                await self.client.send_voice(
                    target,
                    voice=message.voice.file_id,
                    caption=cleaned["text"],
                    caption_entities=cleaned["entities"],
                )
            elif message.animation:
                await self.client.send_animation(
                    target,
                    animation=message.animation.file_id,
                    caption=cleaned["text"],
                    caption_entities=cleaned["entities"],
                )
            elif message.sticker:
                await self.client.send_sticker(
                    target,
                    sticker=message.sticker.file_id,
                )
            elif message.video_note:
                await self.client.send_video_note(
                    target,
                    video_note=message.video_note.file_id,
                )
            elif message.text or message.caption:
                await self.client.send_message(
                    target,
                    cleaned["text"],
                    entities=cleaned["entities"],
                )

            logger.info("Forwarded msg %d → %s", message.id, target)

        except Exception as e:
            logger.error("Failed to forward message %d: %s", message.id, e)
