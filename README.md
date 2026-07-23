# Telegram Forwarder Bot

A production-ready Telegram userbot that automatically forwards posts from multiple source channels to a target channel, with a beautiful inline-button management panel.

## Features

- **Multi-source forwarding** — Monitor unlimited public channels simultaneously
- **All media types** — Text, photos, videos, documents, audio, voice, animations, media groups (albums)
- **Message cleaning** — Automatically strips "Forwarded from" headers, @usernames, watermarks, ads, and separator lines
- **Inline management panel** — Glass-style buttons for adding/removing sources, toggling, status, and more
- **Persistent storage** — Sources and settings survive restarts via JSON files
- **24/7 operation** — Built for VPS deployment with auto-reconnect and flood control

## Requirements

- Python 3.11+
- A Telegram API ID and hash ([get them here](https://my.telegram.org))
- A Telegram account (this is a userbot, not a bot bot)

## Setup

### 1. Clone & configure

```bash
git clone https://github.com/youruser/telegram-forwarder.git
cd telegram-forwarder
cp .env.example .env
```

Edit `.env` with your credentials:

```env
API_ID=12345678
API_HASH=your_api_hash_here
SESSION_NAME=forwarder_session
TARGET_CHANNEL=@your_target_channel
OWNER_ID=123456789
```

### 2. Install dependencies

```bash
python -m venv venv
source venv/bin/activate   # Linux/Mac
# or: venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 3. First run (session login)

```bash
python -m bot.main
```

On first run, you'll be prompted for your Telegram phone number and a verification code. This creates `data/forwarder_session.session` — keep this file safe.

### 4. Open the management panel

Send `/start` or `/panel` to your Telegram account (the one in `OWNER_ID`) to see the management panel.

## Docker

```bash
cp .env.example .env
# Edit .env
docker-compose up -d
```

Check logs:
```bash
docker-compose logs -f
```

## Usage

### Adding a source

1. Click **➕ Add Source** in the panel
2. Send the channel username (`@channelname`) or link (`https://t.me/channelname`)
3. The bot verifies access and adds it

### Removing a source

Click **➖ Remove Source**, then pick a channel from the list.

### Changing the target

Click **🎯 Change Target** and send the new channel username or numeric ID.

### Toggle on/off

Click **⚡ Toggle Forwarding** to enable or disable all forwarding instantly.

### View status

Click **📊 Status** to see current settings at a glance.

## Project Structure

```
telegram-forwarder/
├── bot/
│   ├── __init__.py       # Package init
│   ├── main.py           # Entry point — starts Pyrogram, registers handlers
│   ├── config.py          # Loads .env configuration
│   ├── forwarder.py       # Core forwarding logic (media groups, cleaning)
│   ├── handlers.py        # All command and callback handlers
│   ├── keyboard.py        # Inline keyboard layouts
│   ├── database.py        # JSON-file persistence for sources/settings
│   └── utils.py           # Logger setup, message cleaning, helpers
├── data/                   # Runtime data (sessions, sources.json, settings.json)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

## systemd (optional)

To run as a system service:

```ini
# /etc/systemd/system/forwarder.service
[Unit]
Description=Telegram Forwarder Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/telegram-forwarder
ExecStart=/path/to/venv/bin/python -m bot.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable forwarder
sudo systemctl start forwarder
sudo journalctl -u forwarder -f
```

## Important Notes

- This is a **userbot** (session-based), not a bot token bot. The session represents YOUR Telegram account.
- The userbot account must have **joined** all source channels.
- The target channel must be **accessible** by the userbot account.
- The `OWNER_ID` in `.env` must match your Telegram user ID (use [@userinfobot](https://t.me/userinfobot) to find it).
- Keep `data/forwarder_session.session` private — it grants full access to your account.

## License

MIT
