import re
import logging
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery
from pyrogram.enums import ParseMode

from bot.config import Config
from bot.database import Database
from bot.keyboard import Keyboards

logger = logging.getLogger(__name__)

# Pending conversations: owner_id -> {"action": ..., "data": ...}
_pending: dict[int, dict] = {}


def is_owner(user_id: int) -> bool:
    return user_id == Config.OWNER_ID


def register_handlers(app: Client, db: Database):
    """Register all command and callback handlers."""

    # ── /start & /panel ──────────────────────────────────────────────

    @app.on_message(filters.command(["start", "panel"]) & filters.private)
    async def cmd_start(client: Client, message: Message):
        if not is_owner(message.from_user.id):
            return await message.reply("⛔ You are not authorized to use this bot.")
        await message.reply(
            "Welcome to **Telegram Forwarder Bot**\n\n"
            "Use the buttons below to manage forwarding.",
            reply_markup=Keyboards.main_menu(),
            parse_mode=ParseMode.MARKDOWN,
        )

    # ── Callback router ──────────────────────────────────────────────

    @app.on_callback_query(filters.regex(r"^(back_main|noop)$"))
    async def cb_back(client: Client, cb: CallbackQuery):
        if not is_owner(cb.from_user.id):
            return await cb.answer("Not authorized", show_alert=True)
        if cb.data == "noop":
            return await cb.answer()
        _pending.pop(cb.from_user.id, None)
        await cb.edit_message_text(
            "Welcome to **Telegram Forwarder Bot**\n\n"
            "Use the buttons below to manage forwarding.",
            reply_markup=Keyboards.main_menu(),
            parse_mode=ParseMode.MARKDOWN,
        )

    # ── Add Source ───────────────────────────────────────────────────

    @app.on_callback_query(filters.regex(r"^add_source$"))
    async def cb_add_source(client: Client, cb: CallbackQuery):
        if not is_owner(cb.from_user.id):
            return await cb.answer("Not authorized", show_alert=True)
        _pending[cb.from_user.id] = {"action": "add_source"}
        await cb.edit_message_text(
            "➕ **Add Source Channel**\n\n"
            "Send the channel **username** or **link**.\n"
            "Examples: `@channelname` or `https://t.me/channelname`",
            reply_markup=Keyboards.cancel_button(),
            parse_mode=ParseMode.MARKDOWN,
        )

    # ── Remove Source ────────────────────────────────────────────────

    @app.on_callback_query(filters.regex(r"^remove_source$"))
    async def cb_remove_source(client: Client, cb: CallbackQuery):
        if not is_owner(cb.from_user.id):
            return await cb.answer("Not authorized", show_alert=True)
        sources = db.get_sources()
        if not sources:
            return await cb.answer("No sources to remove", show_alert=True)
        await cb.edit_message_text(
            "➖ **Remove Source Channel**\n\nSelect a channel to remove:",
            reply_markup=Keyboards.source_list_keyboard(sources),
            parse_mode=ParseMode.MARKDOWN,
        )

    @app.on_callback_query(filters.regex(r"^confirm_rm_(-?\d+)$"))
    async def cb_confirm_remove(client: Client, cb: CallbackQuery):
        if not is_owner(cb.from_user.id):
            return await cb.answer("Not authorized", show_alert=True)
        channel_id = int(cb.matches[0].group(1))
        sources = db.get_sources()
        source = next((s for s in sources if s["id"] == channel_id), None)
        if not source:
            return await cb.answer("Channel not found", show_alert=True)
        db.remove_source(channel_id)
        await cb.edit_message_text(
            f"✅ **Removed**: `{source.get('title', str(channel_id))}`",
            reply_markup=Keyboards.back_button(),
            parse_mode=ParseMode.MARKDOWN,
        )

    # ── List Sources ─────────────────────────────────────────────────

    @app.on_callback_query(filters.regex(r"^list_sources$"))
    async def cb_list_sources(client: Client, cb: CallbackQuery):
        if not is_owner(cb.from_user.id):
            return await cb.answer("Not authorized", show_alert=True)
        sources = db.get_sources()
        if not sources:
            text = "📋 **No source channels configured.**"
        else:
            lines = [f"📋 **Source Channels** ({len(sources)})\n"]
            for i, s in enumerate(sources, 1):
                name = s.get("title", "Unknown")
                uname = s.get("username", "")
                uid = f" (@{uname})" if uname else ""
                lines.append(f"  {i}. **{name}**{uid}")
            text = "\n".join(lines)
        await cb.edit_message_text(
            text, reply_markup=Keyboards.back_button(), parse_mode=ParseMode.MARKDOWN
        )

    # ── Change Target ────────────────────────────────────────────────

    @app.on_callback_query(filters.regex(r"^change_target$"))
    async def cb_change_target(client: Client, cb: CallbackQuery):
        if not is_owner(cb.from_user.id):
            return await cb.answer("Not authorized", show_alert=True)
        _pending[cb.from_user.id] = {"action": "change_target"}
        current = db.get_target_channel()
        await cb.edit_message_text(
            f"🎯 **Change Target Channel**\n\n"
            f"Current: `{current}`\n\n"
            "Send the new target channel **username** or **chat ID**.",
            reply_markup=Keyboards.cancel_button(),
            parse_mode=ParseMode.MARKDOWN,
        )

    # ── Toggle Forwarding ────────────────────────────────────────────

    @app.on_callback_query(filters.regex(r"^toggle_forwarding$"))
    async def cb_toggle(client: Client, cb: CallbackQuery):
        if not is_owner(cb.from_user.id):
            return await cb.answer("Not authorized", show_alert=True)
        await cb.edit_message_text(
            "⚡ **Toggle Forwarding**\n\nClick below to switch:",
            reply_markup=Keyboards.toggle_keyboard(db.is_enabled()),
            parse_mode=ParseMode.MARKDOWN,
        )

    @app.on_callback_query(filters.regex(r"^toggle_forwarding_confirm$"))
    async def cb_toggle_confirm(client: Client, cb: CallbackQuery):
        if not is_owner(cb.from_user.id):
            return await cb.answer("Not authorized", show_alert=True)
        new_state = not db.is_enabled()
        db.set_enabled(new_state)
        label = "🟢 Enabled" if new_state else "🔴 Disabled"
        await cb.edit_message_text(
            f"⚡ **Forwarding** set to **{label}**",
            reply_markup=Keyboards.toggle_keyboard(new_state),
            parse_mode=ParseMode.MARKDOWN,
        )

    # ── Status ───────────────────────────────────────────────────────

    @app.on_callback_query(filters.regex(r"^status$"))
    async def cb_status(client: Client, cb: CallbackQuery):
        if not is_owner(cb.from_user.id):
            return await cb.answer("Not authorized", show_alert=True)
        state = "🟢 ON" if db.is_enabled() else "🔴 OFF"
        count = db.get_source_count()
        target = db.get_target_channel()
        await cb.edit_message_text(
            "📊 **Bot Status**\n\n"
            f"  ⚡ Forwarding: **{state}**\n"
            f"  📡 Sources: **{count}**\n"
            f"  🎯 Target: `{target}`\n",
            reply_markup=Keyboards.back_button(),
            parse_mode=ParseMode.MARKDOWN,
        )

    # ── Help ─────────────────────────────────────────────────────────

    @app.on_callback_query(filters.regex(r"^help$"))
    async def cb_help(client: Client, cb: CallbackQuery):
        if not is_owner(cb.from_user.id):
            return await cb.answer("Not authorized", show_alert=True)
        await cb.edit_message_text(
            "❓ **How to Use**\n\n"
            "**1. Add Source** — Add a public channel to monitor.\n"
            "**2. Remove Source** — Remove a channel from monitoring.\n"
            "**3. List Sources** — View all active source channels.\n"
            "**4. Change Target** — Set the channel where posts land.\n"
            "**5. Toggle** — Enable/disable forwarding instantly.\n"
            "**6. Status** — Quick overview of your setup.\n\n"
            "The bot forwards **all new posts** automatically.\n"
            "Forwarded posts are cleaned of watermarks, ads, and source info.",
            reply_markup=Keyboards.back_button(),
            parse_mode=ParseMode.MARKDOWN,
        )

    # ── Text message handler for pending actions ─────────────────────

    @app.on_message(filters.private & filters.text & ~filters.command(["start", "panel"]))
    async def handle_text(client: Client, message: Message):
        if not is_owner(message.from_user.id):
            return
        pending = _pending.pop(message.from_user.id, None)
        if not pending:
            return

        if pending["action"] == "add_source":
            await _process_add_source(client, message, db)
        elif pending["action"] == "change_target":
            await _process_change_target(client, message, db)


async def _process_add_source(client: Client, message: Message, db: Database):
    raw = message.text.strip()
    match = re.search(r"(?:https?://t\.me/|@)(\w+)", raw)
    if not match:
        return await message.reply(
            "❌ Invalid format. Send `@username` or `https://t.me/username`",
            reply_markup=Keyboards.cancel_button(),
            parse_mode=ParseMode.MARKDOWN,
        )

    username = match.group(1)
    try:
        chat = await client.get_chat(username)
    except Exception as e:
        return await message.reply(
            f"❌ Could not access channel: `{e}`\n\n"
            "Make sure the channel is **public** and the userbot account has joined it.",
            reply_markup=Keyboards.cancel_button(),
            parse_mode=ParseMode.MARKDOWN,
        )

    if db.add_source(chat.id, chat.title, getattr(chat, "username", None)):
        await message.reply(
            f"✅ **Added**: {chat.title}\n`ID: {chat.id}`",
            reply_markup=Keyboards.back_button(),
            parse_mode=ParseMode.MARKDOWN,
        )
    else:
        await message.reply(
            "⚠️ This channel is **already** in your source list.",
            reply_markup=Keyboards.back_button(),
            parse_mode=ParseMode.MARKDOWN,
        )


async def _process_change_target(client: Client, message: Message, db: Database):
    raw = message.text.strip()
    match = re.search(r"(?:https?://t\.me/|@)(\w+)", raw)
    if match:
        channel_str = match.group(1)
    else:
        try:
            int(raw)
            channel_str = raw
        except ValueError:
            return await message.reply(
                "❌ Invalid format. Send `@username` or a numeric chat ID.",
                reply_markup=Keyboards.cancel_button(),
                parse_mode=ParseMode.MARKDOWN,
            )

    try:
        await client.get_chat(channel_str if match else int(channel_str))
    except Exception as e:
        return await message.reply(
            f"❌ Could not access channel: `{e}`\n\n"
            "Make sure the channel is **public** or use the correct numeric ID.",
            reply_markup=Keyboards.cancel_button(),
            parse_mode=ParseMode.MARKDOWN,
        )

    display = channel_str if not match else f"@{channel_str}"
    db.set_target_channel(display)
    await message.reply(
        f"✅ **Target changed** to `{display}`",
        reply_markup=Keyboards.back_button(),
        parse_mode=ParseMode.MARKDOWN,
    )
