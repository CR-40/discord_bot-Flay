# 🛡️ Flay — Discord Server Policing Bot

**Flay** is an automated moderation bot designed to enforce server rules without requiring constant human intervention. It is currently tailored for **“The Elites” Discord server**, where it enforces a **media-only rule** in a designated memes channel.

---

## 🚀 What Flay Does

Flay monitors a specific Discord channel and ensures that every message follows the server’s media rule.

### ✅ A message is allowed if it:

- Contains an image, video, or GIF attachment **or**
- Is posted inside a thread **or**
- Already has a thread attached to it

### ❌ If a message violates the rule (no media & no thread), Flay will:

1. **Delete the message**
2. **Timeout the user** (default: 1 minute)
3. **Send a warning via DM**
   - If the user has DMs disabled, the warning is posted in the channel instead

---

## 🧠 How It Works (High Level)

1. The bot listens to all messages in the server.
2. If the message is not in the monitored channel, it is ignored.
3. If the message is in the monitored channel:
   - It checks for media attachments.
   - It checks whether the message is in a thread or has a thread attached.
4. If both checks fail, moderation actions are applied automatically.

---

## ⚙️ Configuration

You can modify these values in the code:

### Change the monitored channel:

```python
MONITORED_CHANNEL_ID = 123456789  # Replace with your channel ID
```

### Change the Timeout Duration:

```python
TIMEOUT_DURATION = timedelta(minutes=1)
```

---

## 🧩 Guild Admin Interface (Per-Guild Controls)

Flay now supports per-guild configuration through admin commands.

### Admin commands

- `!guild_config` → Shows current guild settings
- `!add_monitored #channel` → Adds a channel to monitored list
- `!remove_monitored #channel` → Removes a monitored channel
- `!set_timeout <minutes>` → Sets timeout duration for that guild (1-60)
- `!set_log_channel #channel` → Sets a guild log channel for moderation/config events
- `!show_logs [limit]` → Shows recent in-memory log events for that guild (max 20)

All commands require Administrator permission.
