import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
from datetime import timedelta


# Create bot instance with necessary intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Configuration
MONITORED_CHANNEL_ID = 123456789  # Replace with your channel ID
TIMEOUT_DURATION = timedelta(minutes=1)  # Adjust timeout duration as needed

@bot.event
async def on_ready():
    print(f'{bot.user} is now running!')

@bot.event
async def on_message(message):
    # Ignore bot messages
    if message.author.bot:
        return
    
    # Check if message is in the monitored channel
    if message.channel.id != 1462143382133674212:
        print(f"Message not in monitored channel (Channel ID: {message.channel.id})")
        return
    
    print(f"✓ Message received in monitored channel from {message.author}")
    
    # Check if message is in a thread
    if isinstance(message.channel, discord.Thread):
        print(f"✓ Message is inside a thread, preserving it")
        return
    
    # Fetch the message to get updated thread information
    try:
        fetched_message = await message.channel.fetch_message(message.id)
        if fetched_message.thread is not None:
            print(f"✓ Message has a thread attached, preserving it")
            return
        print(f"✓ Message does not have a thread")
        
    except Exception as e:
        print(f"✗ Error fetching message: {e}")

    # Check if message has any attachments with images or videos
    media_extensions = ('.mp4', '.mov', '.webm', '.mkv', '.avi', '.flv', '.wmv', '.gif')
    has_media = any(
        (
            attachment.content_type and (
                attachment.content_type.startswith('image/') or
                attachment.content_type.startswith('video/')
            )
        ) or (attachment.filename and attachment.filename.lower().endswith(media_extensions))
        for attachment in message.attachments
    )

    print(f"✓ Media check completed - Has media: {has_media}")

    # If no media, delete message and timeout user
    if not has_media:
        try:
            # Store user info before deletion
            user = message.author
            
            print(f"→ Deleting message from {user}...")
            # Delete the message
            await message.delete()
            print(f"✓ Message deleted successfully")
            
            print(f"→ Timing out user {user}...")
            # Timeout the member
            await user.timeout(TIMEOUT_DURATION, reason="Posted message without media in media-only channel")
            print(f"✓ User timed out for {TIMEOUT_DURATION.total_seconds() / 60:.0f} minutes")
            
            print(f"→ Sending warning message...")
            # Construct DM-first warning text mentioning channel and duration
            warning_text = (
                f"You were timed out for {int(TIMEOUT_DURATION.total_seconds() / 60)} minutes "
                f"for posting without media in {message.channel.mention}. "
                "Messages in that channel must include an image, media file or thread."
            )
            try:
                await user.send(warning_text)
                print(f"✓ Warning sent to {user} via DM")
            except discord.Forbidden:
                # User has DMs disabled or blocked the bot — fall back to channel
                print(f"✗ Could not DM {user} (Forbidden). Falling back to channel message.")
                warning_msg = await message.channel.send(f"{user.mention} {warning_text}")
                print(f"✓ Warning message sent in channel")
            except Exception as e:
                print(f"✗ Error sending warning: {e}")
            
            # Optionally delete the warning after some time
            # await warning_msg.delete(delay=10)
            
        except discord.Forbidden:
            print(f"✗ Missing permissions to timeout {user}")
        except Exception as e:
            print(f"✗ Error: {e}")

# Run the bot
load_dotenv()
bot.run(os.getenv('DISCORD_TOKEN'))