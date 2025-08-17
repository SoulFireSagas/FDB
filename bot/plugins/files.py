# bot/plugins/files.py

from telethon import Button
from telethon.events import NewMessage
from telethon.errors import MessageAuthorRequiredError, MessageNotModifiedError, MessageIdInvalidError
from telethon.tl.custom import Message
from secrets import token_hex
from bot import TelegramBot
from bot.config import Telegram, Server
from bot.modules.decorators import verify_user
from bot.modules.telegram import send_message, filter_files, get_file_properties
from bot.modules.static import *
from urllib.parse import quote
import json
import re
from bot.modules.database import db # New Import

# In-memory storage for bulk uploads.
bulk_uploads = {}

@TelegramBot.on(NewMessage(incoming=True, pattern='/bulk'))
@verify_user(private=True)
async def start_bulk_upload(event: NewMessage.Event | Message):
    """
    Starts the bulk upload process by parsing name and text.
    """
    user_id = event.sender_id
    
    # Use a regex to extract name and text from the command
    match = re.search(r'/bulk name:(.*?) text:(.*)', event.text, re.DOTALL)
    
    if not match:
        await event.reply("Please use the format: /bulk name:[name] text:[text]")
        return
    
    name = match.group(1).strip()
    text = match.group(2).strip()

    if not name or not text:
        await event.reply("Both name and text fields must not be empty.")
        return

    # Initialize the bulk_uploads dictionary for the user
    bulk_uploads[user_id] = {'name': name, 'text': text, 'files': []}
    
    await event.reply(
        f"Bulk upload started.\nName: **{name}**\nText: **{text}**\n\nNow, send me your files. When you're done, use the /bulk_end command."
    )

@TelegramBot.on(NewMessage(incoming=True, func=filter_files))
@verify_user(private=True)
async def user_file_handler(event: NewMessage.Event | Message):
    """
    Handles user file uploads and either adds them to the bulk list or
    creates a single-file link.
    """
    user_id = event.sender_id
    
    # Check if the user is in bulk upload mode
    if user_id in bulk_uploads:
        file = event.message
        
        # Generate and save the secret code for each file
        secret_code = token_hex(Telegram.SECRET_CODE_LENGTH)
        file.text = f'`{secret_code}`'
        message = await send_message(file)
        
        # Get file properties from the new message object
        file_name, file_size, mime_type = get_file_properties(message)
        
        file_info = {'id': message.id, 'size': file_size, 'secret_code': secret_code}
        bulk_uploads[user_id]['files'].append(file_info)
        
        file_count = len(bulk_uploads[user_id]['files'])
        await event.reply(f"File {file_count} added to bulk list.")
    else:
        # Your original single file handler logic
        secret_code = token_hex(Telegram.SECRET_CODE_LENGTH)
        event.message.text = f'`{secret_code}`'
        message = await send_message(event.message)
        message_id = message.id
        
        # Save the file metadata to MongoDB
        db.save_file(message_id, secret_code)

        dl_link = f'{Server.BASE_URL}/RD/{message_id}?code={secret_code}'
        tg_link = f'{Server.BASE_URL}/file/{message_id}?code={secret_code}'

        if (event.document and 'video' in event.document.mime_type) or event.video:
             await event.reply(
                 message=MediaLinksText % {'dl_link': dl_link}, 
                 buttons=[
                     [
                         Button.url('Download', dl_link)
                     ]
                 ]
             )
        else:
            await event.reply(
                message=FileLinksText % {'dl_link': dl_link, 'tg_link': tg_link},
                buttons=[
                    [
                        Button.url('Download', dl_link)
                    ]
                ]
            )

@TelegramBot.on(NewMessage(incoming=True, pattern='/bulk_end'))
@verify_user(private=True)
async def end_bulk_upload(event: NewMessage.Event | Message):
    """
    Ends the bulk upload, generates the link, and clears the user's state.
    """
    user_id = event.sender_id
    
    if user_id not in bulk_uploads or not bulk_uploads[user_id]['files']:
        await event.reply("No files were uploaded. Please use /bulk to start.")
        return
        
    bulk_data = bulk_uploads[user_id]
    del bulk_uploads[user_id]
    
    # Save bulk data to MongoDB instead of the channel
    bulk_id = db.save_bulk(bulk_data)
    
    bulk_link = f"{Server.BASE_URL}/Episodes/{bulk_id}"
    
    await event.reply(
        "Bulk upload complete! Here is your dedicated page:\n\n"
        f"🔗 **Link:** {bulk_link}\n\n"
        "This link is now permanent and will not expire."
    )

@TelegramBot.on(NewMessage(incoming=True, func=filter_files, forwards=False))
@verify_user()
async def channel_file_handler(event: NewMessage.Event | Message):
    """
    Handles new files in the channel, adding download links.
    """
    # Check if the message was sent by the bot itself by checking the sender ID
    me = await TelegramBot.get_me()
    if event.sender_id == me.id:
        try:
            # We no longer need to edit the message here, as it's a file sent by a human user
            pass
        except (
            MessageAuthorRequiredError,
            MessageIdInvalidError,
            MessageNotModifiedError,
        ):
            pass
        return
    
    # If the message was sent by a user, add the download button
    secret_code = token_hex(Telegram.SECRET_CODE_LENGTH)
    
    # We save the metadata to MongoDB instead of adding it to the message text
    db.save_file(event.message.id, secret_code)

    try:
        await event.edit(
            buttons=[
                [Button.url("Download", f'{Server.BASE_URL}/RD/{event.message.id}?code={secret_code}')]
            ]
        )
    except (
        MessageAuthorRequiredError,
        MessageIdInvalidError,
        MessageNotModifiedError,
    ):
        pass

