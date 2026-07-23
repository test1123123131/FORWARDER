import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Telegram API
    API_ID = int(os.getenv("API_ID", 0))
    API_HASH = os.getenv("API_HASH", "")
    SESSION_NAME = os.getenv("SESSION_NAME", "forwarder_session")
    SESSION_STRING = os.getenv("SESSION_STRING", "")

    # Target channel
    TARGET_CHANNEL = os.getenv("TARGET_CHANNEL", "")

    # Owner
    OWNER_ID = int(os.getenv("OWNER_ID", 0))

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # Paths
    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    SOURCES_FILE = os.path.join(DATA_DIR, "sources.json")
    SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")

    @classmethod
    def validate(cls):
        errors = []
        if not cls.API_ID:
            errors.append("API_ID is not set")
        if not cls.API_HASH:
            errors.append("API_HASH is not set")
        if not cls.OWNER_ID:
            errors.append("OWNER_ID is not set")
        if errors:
            raise ValueError("Config errors: " + ", ".join(errors))
