import json
import os
from collections import deque
from datetime import datetime, timedelta, timezone

import discord
from discord.ext import commands
from dotenv import load_dotenv

import check
from logger_config import logger

CONFIG_FILE = 'data.json'
DEFAULT_TIMEOUT_MINUTES = 1
EVENT_LOG_LIMIT = 200

# In-memory runtime stores
GUILD_SETTINGS: dict[int, dict] = {}
GUILD_EVENT_LOGS: dict[int, deque[str]] = {}

# Create bot instance with necessary intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)


def _default_guild_settings(guild_id: int, guild_name: str = 'Unknown') -> dict:
    return {
        'guild_id': guild_id,
        'guild_name': guild_name,
        'monitored_channel_ids': [],
        'timeout_minutes': DEFAULT_TIMEOUT_MINUTES,
        'log_channel_id': None,
    }


def load_guild_settings() -> dict[int, dict]:
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        settings: dict[int, dict] = {}
        for guild_cfg in data:
            guild_id = guild_cfg.get('guild_id')
            if not guild_id:
                continue

            settings[guild_id] = {
                'guild_id': guild_id,
                'guild_name': guild_cfg.get('guild_name', 'Unknown'),
                'monitored_channel_ids': guild_cfg.get('monitored_channel_ids', []),
                'timeout_minutes': guild_cfg.get('timeout_minutes', DEFAULT_TIMEOUT_MINUTES),
                'log_channel_id': guild_cfg.get('log_channel_id'),
            }

        logger.info('Loaded settings for %s guild(s) from %s.', len(settings), CONFIG_FILE)
        return settings
    except FileNotFoundError:
        logger.warning('%s not found. Starting with empty guild settings.', CONFIG_FILE)
        return {}
    except Exception:
        logger.exception('Error loading guild settings from %s.', CONFIG_FILE)
        return {}


def save_guild_settings() -> None:
    payload = list(GUILD_SETTINGS.values())
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=4)


def get_guild_settings(guild: discord.Guild) -> dict:
    settings = GUILD_SETTINGS.get(guild.id)
    if settings is None:
        settings = _default_guild_settings(guild.id, guild.name)
        GUILD_SETTINGS[guild.id] = settings
        save_guild_settings()
        logger.info('Created default settings for guild %s (%s).', guild.name, guild.id)
    return settings


def get_guild_event_log(guild_id: int) -> deque[str]:
    if guild_id not in GUILD_EVENT_LOGS:
        GUILD_EVENT_LOGS[guild_id] = deque(maxlen=EVENT_LOG_LIMIT)
    return GUILD_EVENT_LOGS[guild_id]


async def record_guild_event(guild: discord.Guild, text: str) -> None:
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    entry = f'[{timestamp}] {text}'
    get_guild_event_log(guild.id).append(entry)
    logger.info('[%s] %s', guild.name, text)

    settings = get_guild_settings(guild)
    log_channel_id = settings.get('log_channel_id')
    if log_channel_id:
        channel = guild.get_channel(log_channel_id)
        if isinstance(channel, discord.TextChannel):
            try:
                await channel.send(f'`{entry}`')
            except Exception:
                logger.exception('Failed to send guild log to channel %s in guild %s.', log_channel_id, guild.id)


def format_guild_config(guild: discord.Guild, settings: dict) -> str:
    monitored_ids = settings.get('monitored_channel_ids', [])
    monitored = ', '.join(f'<#{cid}>' for cid in monitored_ids) if monitored_ids else 'None'
    log_channel = f"<#{settings['log_channel_id']}>" if settings.get('log_channel_id') else 'Not set'

    return (
        f'**Guild:** {guild.name}\n'
        f'**Monitored channels:** {monitored}\n'
        f"**Timeout:** {settings.get('timeout_minutes', DEFAULT_TIMEOUT_MINUTES)} minute(s)\n"
        f'**Log channel:** {log_channel}'
    )


GUILD_SETTINGS = load_guild_settings()


@bot.event
async def on_ready():
    logger.info('%s is now running!', bot.user)


@bot.event
async def on_message(message: discord.Message):
    if not message.guild:
        logger.debug('Ignoring non-guild message (channel_id=%s).', message.channel.id)
        return

    if message.author.bot:
        logger.debug(
            'Ignoring bot message (channel_id=%s, author=%s).',
            message.channel.id,
            message.author,
        )
        return

    if message.content.startswith(str(bot.command_prefix)):
        await bot.process_commands(message)
        return

    settings = get_guild_settings(message.guild)
    monitored_channels = settings.get('monitored_channel_ids', [])

    if message.channel.id not in monitored_channels:
        logger.debug('Ignoring message from non-monitored channel (channel_id=%s).', message.channel.id)
        return

    logger.info('Processing message %s in monitored channel from %s.', message.id, message.author)

    has_thread = await check.message_has_thread(message)
    has_media = await check.message_has_media(message)

    if not (has_media or has_thread):
        user = message.author
        timeout_minutes = settings.get('timeout_minutes', DEFAULT_TIMEOUT_MINUTES)
        timeout_duration = timedelta(minutes=timeout_minutes)

        try:
            warning_text = await generate_warning_text(message, timeout_duration)

            logger.info('Deleting non-compliant message %s from %s.', message.id, user)
            await message.delete()

            if message.author.guild_permissions.administrator:
                issue_report = (
                    f'Issue Report: Your message in {message.channel.mention} was deleted because '
                    'it did not contain media and was not in a thread.'
                )
                await user.send(issue_report)
                await record_guild_event(
                    message.guild,
                    f'Admin message deleted for rule violation: user={user} channel={message.channel.id}',
                )
                return

            await user.timeout(timeout_duration, reason='Posted message without media in media-only channel')
            await user.send(warning_text)
            await record_guild_event(
                message.guild,
                (
                    f'Rule enforcement: user={user} channel={message.channel.id} '
                    f'timeout={timeout_minutes}m message_id={message.id}'
                ),
            )

        except discord.Forbidden:
            logger.exception('Missing permissions while moderating message %s from %s.', message.id, user)
            await record_guild_event(
                message.guild,
                f'Permission error while moderating user={user} channel={message.channel.id}',
            )
        except Exception:
            logger.exception('Unexpected error while moderating message %s.', message.id)
            await record_guild_event(
                message.guild,
                f'Unexpected moderation error for user={user} message_id={message.id}',
            )

    logger.info('Message processing completed for message %s.', message.id)


async def generate_warning_text(message: discord.Message, timeout_duration: timedelta) -> str:
    """Generate warning text based on context."""
    return (
        f'You were timed out for {int(timeout_duration.total_seconds() / 60)} minutes '
        f'for posting without media in {message.channel.mention}. '
        'Messages in that channel must include an image, media file or thread.'
    )


@bot.command(name='guild_config')
@commands.has_permissions(administrator=True)
async def guild_config(ctx: commands.Context):
    settings = get_guild_settings(ctx.guild)
    await ctx.send(format_guild_config(ctx.guild, settings))


@bot.command(name='add_monitored')
@commands.has_permissions(administrator=True)
async def add_monitored(ctx: commands.Context, channel: discord.TextChannel):
    settings = get_guild_settings(ctx.guild)
    monitored = settings['monitored_channel_ids']

    if channel.id in monitored:
        await ctx.send(f'{channel.mention} is already monitored.')
        return

    monitored.append(channel.id)
    save_guild_settings()
    await record_guild_event(ctx.guild, f'Config update: added monitored channel {channel.id} by {ctx.author}')
    await ctx.send(f'Added {channel.mention} to monitored channels.')


@bot.command(name='remove_monitored')
@commands.has_permissions(administrator=True)
async def remove_monitored(ctx: commands.Context, channel: discord.TextChannel):
    settings = get_guild_settings(ctx.guild)
    monitored = settings['monitored_channel_ids']

    if channel.id not in monitored:
        await ctx.send(f'{channel.mention} is not in monitored channels.')
        return

    monitored.remove(channel.id)
    save_guild_settings()
    await record_guild_event(ctx.guild, f'Config update: removed monitored channel {channel.id} by {ctx.author}')
    await ctx.send(f'Removed {channel.mention} from monitored channels.')


@bot.command(name='set_timeout')
@commands.has_permissions(administrator=True)
async def set_timeout(ctx: commands.Context, minutes: int):
    if minutes < 1 or minutes > 60:
        await ctx.send('Timeout must be between 1 and 60 minutes.')
        return

    settings = get_guild_settings(ctx.guild)
    settings['timeout_minutes'] = minutes
    save_guild_settings()
    await record_guild_event(ctx.guild, f'Config update: timeout set to {minutes}m by {ctx.author}')
    await ctx.send(f'Timeout updated to {minutes} minute(s).')


@bot.command(name='set_log_channel')
@commands.has_permissions(administrator=True)
async def set_log_channel(ctx: commands.Context, channel: discord.TextChannel):
    settings = get_guild_settings(ctx.guild)
    settings['log_channel_id'] = channel.id
    save_guild_settings()
    await record_guild_event(ctx.guild, f'Config update: log channel set to {channel.id} by {ctx.author}')
    await ctx.send(f'Log channel set to {channel.mention}.')


@bot.command(name='show_logs')
@commands.has_permissions(administrator=True)
async def show_logs(ctx: commands.Context, limit: int = 10):
    limit = max(1, min(limit, 20))
    entries = list(get_guild_event_log(ctx.guild.id))[-limit:]

    if not entries:
        await ctx.send('No runtime log entries are available for this guild yet.')
        return

    content = '\n'.join(entries)
    await ctx.send(f'Last {len(entries)} log entries:\n```\n{content}\n```')


@guild_config.error
@add_monitored.error
@remove_monitored.error
@set_timeout.error
@set_log_channel.error
@show_logs.error
async def admin_command_error(ctx: commands.Context, error: Exception):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send('You need administrator permissions to use this command.')
        return

    logger.exception('Command error in %s: %s', ctx.command, error)
    await ctx.send('Something went wrong while processing that command.')


# Run the bot
if __name__ == '__main__':
    load_dotenv()
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error('DISCORD_TOKEN not found. Please check your .env file.')
    else:
        bot.run(token)
