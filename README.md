# 🛡️ Flay — Discord Server Policing Bot

**Flay** is an automated Discord moderation bot that enforces a **media-only rule** in configured channels.
It supports **per-guild settings** so each server can manage its own monitored channels, timeout duration, and moderation log channel.

---

## 🚀 What Flay Does

In monitored channels, a message is allowed if it:

- Contains image/video/GIF media attachment, **or**
- Is posted inside a thread, **or**
- Has an associated thread.

If a message violates the rule, Flay will:

1. Delete the message
2. Timeout the user (guild-configurable)
3. Send a DM warning to the user

---

## ⚙️ Requirements

- Python 3.10+
- Dependencies from `requirements.txt`

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 🔐 Environment Variables

Create a `.env` file:

```env
DISCORD_TOKEN=your_bot_token_here
```

---

## 🗂️ Data Configuration (`data.json`)

Flay stores per-guild configuration in `data.json`.

Example:

```json
[
  {
    "guild_name": "The Elites",
    "guild_id": 1361226165695676498,
    "monitored_channel_ids": [1361226165695676501],
    "timeout_minutes": 1,
    "log_channel_id": 1361226165695676502
  }
]
```

### Fields

- `guild_name`: Human-readable guild name
- `guild_id`: Discord guild ID
- `monitored_channel_ids`: List of channels where media-only rule is enforced
- `timeout_minutes` *(optional, default: 1)*: Timeout duration for violations
- `log_channel_id` *(optional)*: Channel where moderation/config events are posted

---

## 🧩 Guild Admin Commands

All commands below require **Administrator** permissions.

- `!guild_config`  
  Show current guild configuration.

- `!add_monitored #channel`  
  Add a channel to monitored channels for this guild.

- `!remove_monitored #channel`  
  Remove a channel from monitored channels for this guild.

- `!set_timeout <minutes>`  
  Set timeout duration (1 to 60 minutes).

- `!set_log_channel #channel`  
  Set the guild channel that receives moderation/config event logs.

- `!show_logs [limit]`  
  Show recent in-memory guild log entries (up to 20).

---

## ▶️ Run

```bash
python main.py
```

---

## 📝 Logging

Flay uses centralized logging (console + `bot.log`) and additionally supports per-guild event logs via `!show_logs` and optional forwarding with `!set_log_channel`.
