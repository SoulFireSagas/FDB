from telethon import Button
from telethon.events import NewMessage
from telethon.tl.custom.message import Message
from bot import TelegramBot, logger  # Ensure logger is imported
from bot.config import Telegram
from bot.modules.static import *
from bot.modules.decorators import verify_user
from datetime import datetime

@TelegramBot.on(NewMessage(incoming=True, pattern=r'^/start$'))
@verify_user(private=True)
async def welcome(event: NewMessage.Event | Message):
    try:
        logger.info(
            f"Start command received from {event.sender.id} "
            f"(@{event.sender.username or 'no-username'})"
        )
        
        await event.reply(
            message=WelcomeText % {'first_name': event.sender.first_name},
            buttons=[
                [
                    Button.url('Add to Channel', 
                    f'https://t.me/{Telegram.BOT_USERNAME}?startchannel&admin=post_messages+edit_messages+delete_messages')
                ]
            ]
        )
        logger.debug(f"Start message sent to {event.sender.id}")

    except Exception as e:
        logger.error(
            f"Failed to handle /start for {event.sender.id}: {str(e)}",
            exc_info=True
        )
        await event.respond("❌ Failed to process command. Please try again.")

@TelegramBot.on(NewMessage(incoming=True, pattern=r'^/info$'))
@verify_user(private=True)
async def user_info(event: Message):
    try:
        logger.info(
            f"Info request from {event.sender.id} "
            f"(Name: {event.sender.first_name})"
        )
        
        await event.reply(UserInfoText.format(sender=event.sender))
        logger.debug(f"User info sent to {event.sender.id}")

    except Exception as e:
        logger.error(
            f"User info failed for {event.sender.id}: {str(e)}",
            exc_info=True
        )

@TelegramBot.on(NewMessage(chats=Telegram.OWNER_ID, incoming=True, pattern=r'^/log$'))
async def send_log(event: NewMessage.Event | Message):
    try:
        log_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(
            f"Log request from owner {event.sender.id} at {log_time}"
        )
        
        await event.reply(file='event-log.txt')
        logger.debug("Log file sent successfully")

    except FileNotFoundError:
        logger.warning("Log file not found when requested by owner")
        await event.respond("⚠️ Log file not available yet")
    except Exception as e:
        logger.critical(
            f"CRITICAL: Failed to send logs to owner: {str(e)}",
            exc_info=True
        )
