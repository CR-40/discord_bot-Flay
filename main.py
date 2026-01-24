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
MONITORED_CHANNEL_IDs = [1464534259753685147,1464534335154552997]  # Replace with your channel ID(s)
TIMEOUT_DURATION = timedelta(minutes=1)  # Adjust timeout duration as needed


@bot.event
async def on_ready():
    print(f'{bot.user} is now running!')

@bot.event
async def on_message(message):

    if message.author.bot:
        return

    if  message.channel.id not in MONITORED_CHANNEL_IDs:
        print(f"Message not in monitored channel (Channel ID: {message.channel.id})")
        return
    print(f"✓ Message received in monitored channel from {message.author}")

    # Check if message is in a thread
    has_thread = await message_has_thread(message)
   
    # Check if message has any attachments with images or videos
    has_media = await message_has_media(message)

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
                print(f"✗ User {user} is an administrator; skipping timeout.")
                return
            
            # Timeout the member
            print(f"→ Timing out user {user}...")
            await user.timeout(TIMEOUT_DURATION, reason="Posted message without media in media-only channel")
            print(f"✓ User timed out for {TIMEOUT_DURATION.total_seconds() / 60:.0f} minutes")

        except discord.Forbidden as e:
            print(f"✗ Missing permissions to timeout {user}")
        except Exception as e:
            print(f"✗ Error: {e}")
    print(f"✓ message processing completed")
    print("--------------------------------------------------")



### Helper functions ###
### Check if message has media attachments
async def message_has_media(message):
    has_media = False
    media_extensions = ('.mp4', '.mov', '.webm', '.mkv', '.avi', '.flv', '.wmv', '.gif')
   
    for attachment in message.attachments:
        if attachment.content_type:
            if attachment.content_type.startswith('image/') or attachment.content_type.startswith('video/'):
                has_media = True

        if attachment.filename and attachment.filename.lower().endswith(media_extensions):
            has_media = True
        
    print(f"✓ Media check completed - Has media: {has_media}")
    return has_media

### Check if message is in a thread or has an associated thread
async def message_has_thread(message):
    has_thread = False
    if isinstance(message.channel, discord.Thread):
        has_thread = True
        print(f"✓ Thread check completed - Message is inside a thread")
        return True
    
    try:
        fetched_message = await message.channel.fetch_message(message.id)
        if fetched_message.thread is not None:
            has_thread = True
    except Exception as e:
        print(f"✗ Error checking thread status: {e}")
 
    print(f"✓ Thread check completed - Has thread: {has_thread}")       
    return has_thread
   

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