import os
from dotenv import load_dotenv
from typing import List, Union

load_dotenv()


class Config:
    # Telegram API
    API_ID: int = int(os.getenv("API_ID", "0"))
    API_HASH: str = os.getenv("API_HASH", "")
    PHONE: str = os.getenv("PHONE", "")

    # Channels
    _SOURCE_RAW: str = os.getenv("SOURCE_CHANNELS", "")
    DEST_CHANNEL: str = os.getenv("DEST_CHANNEL", "")

    # Performance
    FORWARD_DELAY: int = int(os.getenv("FORWARD_DELAY", "2"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def get_source_channels(cls) -> List[str]:
        if not cls._SOURCE_RAW.strip():
            return []
        return [ch.strip() for ch in cls._SOURCE_RAW.split(",") if ch.strip()]

    @classmethod
    def validate(cls) -> bool:
        errors = []
        if not cls.API_ID:
            errors.append("API_ID is required")
        if not cls.API_HASH:
            errors.append("API_HASH is required")
        if not cls.PHONE:
            errors.append("PHONE is required")
        if not cls.get_source_channels():
            errors.append("At least one SOURCE_CHANNEL is required")
        if not cls.DEST_CHANNEL:
            errors.append("DEST_CHANNEL is required")
        if errors:
            for e in errors:
                print(f"[CONFIG ERROR] {e}")
            return False
        return True
