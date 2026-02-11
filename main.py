import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
from datetime import timedelta
import check
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),  # Saves to file
        logging.StreamHandler()          # Also prints to console
    ]
)


# Create bot instance with necessary intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)


# Configuration
def load_monitored_channels():
    try:
        with open('data.json', 'r') as f:
            data = json.load(f)
        ids = []
        for guild in data:
            ids.extend(guild.get("monitored_channel_ids", []))
        return ids
    except Exception as e:
        logging.error(f"Error loading monitored channels: {e}") 
        return []

MONITORED_CHANNEL_IDs = load_monitored_channels()
TIMEOUT_DURATION = timedelta(minutes=1)  # Adjust timeout duration as needed


@bot.event
async def on_ready():
    logging.info(f'{bot.user} is now running!')

@bot.event
async def on_message(message):
    if not message.guild:
        logging.info("Ignoring non-guild message (Channel ID: {message.channel.id})")
        return

    if message.author.bot:
        logging.info("Ignoring bot message(Channel ID: {message.channel.id} , Author: {message.author})")
        return

    if message.channel.id not in MONITORED_CHANNEL_IDs:
        logging.info(f"Ignoring message from non-monitored channel (Channel ID: {message.channel.id})")
        return
    print(f"✓ Message received in monitored channel from {message.author}")

    # Check if message is in a thread
    has_thread = await check.message_has_thread(message)
   
    # Check if message has any attachments with images or videos
    has_media = await check.message_has_media(message)

    # Penalties sequence----->>>>
    # If no media, delete message and timeout user
    if not (has_media or has_thread):
        try:
            # Store user info before deletion
            user = message.author
            
            # Generate warning text early so it is available if exceptions occur below
            warning_text = await generate_warning_text(message, ctx=1)
            
            # Delete the message
            print(f"→ Deleting message from {user}...")
            await message.delete()
            print(f"✓ Message deleted successfully")

            if message.guild and message.author.guild_permissions.administrator:
                issue_report = (
                    f'✗ Issue Report: Message from administrator {user} was deleted in {message.channel.mention},'
                    f'for not containing media or not being in a thread.'
                    )
                await user.send(issue_report)
                print(f"✗ User {user} is an administrator; sending issue report...")
                print("------------------------------------------------RC3-")
                return
            
            # Timeout the member
            print(f"→ Timing out user {user}...")
            await user.timeout(TIMEOUT_DURATION, reason="Posted message without media in media-only channel")
            print(f"✓ User timed out for {TIMEOUT_DURATION.total_seconds() / 60:.0f} minutes")

            await user.send(warning_text)
            print(f"✓ Warning message sent to {user}")

        except discord.Forbidden as e:
            print(f"✗ Missing permissions to timeout {user}")
            issue_report = (
                    f'✗ Issue Report: Message from administrator {user} was deleted in {message.channel.mention},'
                    f'for not containing media or not being in a thread.'
                    )
            await user.send(issue_report)
            print(f"✗ User {user} is an administrator; sending issue report...")
            print("------------------------------------------------RC3-")
        except Exception as e:
            print(f"✗ Error: {e}")

    print(f"✓ message processing completed")
    print("-------------------------------------------------cc-")

### Generate warning text based on context
async def generate_warning_text(message, ctx):
    warning_text = ""
    match ctx:
        case 1:
            warning_text = (
                f"You were timed out for {int(TIMEOUT_DURATION.total_seconds() / 60)} minutes "
                f"for posting without media in {message.channel.mention}. "
                "Messages in that channel must include an image, media file or thread."
            )
    return warning_text
    

# Run the bot
if __name__ == "__main__":
    load_dotenv()
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("✗ Error: DISCORD_TOKEN not found. Please check your .env file.")
    else:
        bot.run(token)