import json
import os
import logging
from typing import Optional
from bot.config import Config

logger = logging.getLogger(__name__)


class Database:
    """JSON-file-based persistence for sources and settings."""

    def __init__(self):
        os.makedirs(Config.DATA_DIR, exist_ok=True)
        self._sources: list[dict] = []
        self._settings: dict = {
            "enabled": True,
            "target_channel": Config.TARGET_CHANNEL,
        }
        self._load()

    # ── Sources ───────────────────────────────────────────────────────────

    def _load(self):
        # Load sources
        if os.path.exists(Config.SOURCES_FILE):
            try:
                with open(Config.SOURCES_FILE, "r", encoding="utf-8") as f:
                    self._sources = json.load(f)
                logger.info("Loaded %d source channels", len(self._sources))
            except (json.JSONDecodeError, IOError) as e:
                logger.error("Failed to load sources file: %s", e)
                self._sources = []

        # Load settings
        if os.path.exists(Config.SETTINGS_FILE):
            try:
                with open(Config.SETTINGS_FILE, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    self._settings.update(saved)
                logger.info("Loaded settings")
            except (json.JSONDecodeError, IOError) as e:
                logger.error("Failed to load settings file: %s", e)

    def _save_sources(self):
        try:
            with open(Config.SOURCES_FILE, "w", encoding="utf-8") as f:
                json.dump(self._sources, f, indent=2, ensure_ascii=False)
        except IOError as e:
            logger.error("Failed to save sources: %s", e)

    def _save_settings(self):
        try:
            with open(Config.SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self._settings, f, indent=2, ensure_ascii=False)
        except IOError as e:
            logger.error("Failed to save settings: %s", e)

    def add_source(self, channel_id: int, channel_title: str, username: Optional[str] = None) -> bool:
        if any(s["id"] == channel_id for s in self._sources):
            return False
        entry = {"id": channel_id, "title": channel_title}
        if username:
            entry["username"] = username
        self._sources.append(entry)
        self._save_sources()
        logger.info("Added source: %s (%d)", channel_title, channel_id)
        return True

    def remove_source(self, channel_id: int) -> bool:
        before = len(self._sources)
        self._sources = [s for s in self._sources if s["id"] != channel_id]
        if len(self._sources) < before:
            self._save_sources()
            logger.info("Removed source: %d", channel_id)
            return True
        return False

    def get_sources(self) -> list[dict]:
        return list(self._sources)

    def get_source_ids(self) -> list[int]:
        return [s["id"] for s in self._sources]

    # ── Settings ──────────────────────────────────────────────────────────

    def is_enabled(self) -> bool:
        return self._settings.get("enabled", True)

    def set_enabled(self, value: bool):
        self._settings["enabled"] = value
        self._save_settings()

    def get_target_channel(self) -> str:
        return self._settings.get("target_channel", Config.TARGET_CHANNEL)

    def set_target_channel(self, channel: str):
        self._settings["target_channel"] = channel
        self._save_settings()

    # ── Stats ─────────────────────────────────────────────────────────────

    def get_source_count(self) -> int:
        return len(self._sources)
