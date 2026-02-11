import discord

class check :

    async def channel_monitored(self, message):
        '''Check if message is in a monitored channel'''
        pass

    async def message_has_media(self, message):
        '''Check if message has any attachments with images or videos'''
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
    
    async def message_has_thread(self, message : discord.Message):
        '''Check if message is in a thread or has an associated thread'''
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