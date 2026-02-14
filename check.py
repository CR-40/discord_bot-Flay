import discord

from logger_config import logger


async def message_has_media(message: discord.Message) -> bool:
    """Check if message has any attachments with images or videos."""
    has_media = False
    media_extensions = ('.mp4', '.mov', '.webm', '.mkv', '.avi', '.flv', '.wmv', '.gif')

    for attachment in message.attachments:
        if attachment.content_type and (
            attachment.content_type.startswith('image/')
            or attachment.content_type.startswith('video/')
        ):
            has_media = True
            logger.debug(
                'Media match by content_type for attachment %s in message %s.',
                attachment.filename,
                message.id,
            )

        if attachment.filename and attachment.filename.lower().endswith(media_extensions):
            has_media = True
            logger.debug(
                'Media match by extension for attachment %s in message %s.',
                attachment.filename,
                message.id,
            )

    logger.info('Media check completed for message %s - has_media=%s', message.id, has_media)
    return has_media


async def message_has_thread(message: discord.Message) -> bool:
    """Check if message is in a thread or has an associated thread."""
    has_thread = False

    if isinstance(message.channel, discord.Thread):
        logger.info('Thread check completed for message %s - message is inside a thread.', message.id)
        return True

    try:
        fetched_message = await message.channel.fetch_message(message.id)
        has_thread = fetched_message.thread is not None
    except Exception:
        logger.exception('Error checking thread status for message %s.', message.id)

    logger.info('Thread check completed for message %s - has_thread=%s', message.id, has_thread)
    return has_thread
