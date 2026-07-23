from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


class Keyboards:
    """Glass-style inline keyboard layouts."""

    @staticmethod
    def main_menu() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("➕ Add Source", callback_data="add_source"),
                    InlineKeyboardButton("➖ Remove Source", callback_data="remove_source"),
                ],
                [
                    InlineKeyboardButton("📋 List Sources", callback_data="list_sources"),
                    InlineKeyboardButton("🎯 Change Target", callback_data="change_target"),
                ],
                [
                    InlineKeyboardButton("⚡ Toggle Forwarding", callback_data="toggle_forwarding"),
                    InlineKeyboardButton("📊 Status", callback_data="status"),
                ],
                [
                    InlineKeyboardButton("❓ Help", callback_data="help"),
                ],
            ]
        )

    @staticmethod
    def toggle_keyboard(enabled: bool) -> InlineKeyboardMarkup:
        label = "🟢 ON" if enabled else "🔴 OFF"
        return InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        f"Switch to {'🔴 OFF' if enabled else '🟢 ON'}",
                        callback_data="toggle_forwarding_confirm",
                    )
                ],
                [
                    InlineKeyboardButton(f"Current: {label}", callback_data="noop"),
                ],
                [
                    InlineKeyboardButton("🔙 Back", callback_data="back_main"),
                ],
            ]
        )

    @staticmethod
    def confirm_remove(source_id: int, source_title: str) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        f"Confirm remove: {source_title}",
                        callback_data=f"confirm_rm_{source_id}",
                    )
                ],
                [
                    InlineKeyboardButton("🔙 Cancel", callback_data="back_main"),
                ],
            ]
        )

    @staticmethod
    def source_list_keyboard(sources: list[dict]) -> InlineKeyboardMarkup:
        buttons = []
        for s in sources:
            name = s.get("title", str(s["id"]))[:30]
            buttons.append(
                [InlineKeyboardButton(f"❌ {name}", callback_data=f"confirm_rm_{s['id']}")]
            )
        buttons.append([InlineKeyboardButton("🔙 Back", callback_data="back_main")])
        return InlineKeyboardMarkup(buttons)

    @staticmethod
    def back_button() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 Back", callback_data="back_main")]]
        )

    @staticmethod
    def cancel_button() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            [[InlineKeyboardButton("❌ Cancel", callback_data="back_main")]]
        )
