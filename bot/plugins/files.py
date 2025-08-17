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

# Temporary in-memory storage for bulk uploads.
bulk_uploads = {}

@TelegramBot.on(NewMessage(incoming=True, pattern='/bulk'))
@verify_user(private=True)
async def start_bulk_upload(event: NewMessage.Event | Message):
    """
    Starts the bulk upload process for a user.
    """
    user_id = event.sender_id
    
    # Initialize the bulk_uploads dictionary for the user with empty values
    bulk_uploads[user_id] = {'name': '', 'text': '', 'files': []}
    
    await event.reply(
        "Bulk upload started. Use /bulk_name and /bulk_text to set the details, then send me your files. When you're done, use the /bulk_end command."
    )

@TelegramBot.on(NewMessage(incoming=True, pattern='/bulk_name'))
@verify_user(private=True)
async def set_bulk_name(event: NewMessage.Event | Message):
    """
    Sets the name for the bulk upload.
    """
    user_id = event.sender_id
    parts = event.text.split(' ', 1)
    
    if user_id not in bulk_uploads:
        await event.reply("Please start a bulk upload first with the /bulk command.")
        return
    
    if len(parts) < 2:
        await event.reply("Please provide a name. Example: /bulk_name My Awesome File Collection")
        return
        
    name = parts[1]
    bulk_uploads[user_id]['name'] = name
    
    await event.reply(f"Name set to: **{name}**")

@TelegramBot.on(NewMessage(incoming=True, pattern='/bulk_text'))
@verify_user(private=True)
async def set_bulk_text(event: NewMessage.Event | Message):
    """
    Sets the text for the bulk upload.
    """
    user_id = event.sender_id
    parts = event.text.split(' ', 1)
    
    if user_id not in bulk_uploads:
        await event.reply("Please start a bulk upload first with the /bulk command.")
        return
        
    if len(parts) < 2:
        await event.reply("Please provide text. Example: /bulk_text My File Text")
        return
        
    text = parts[1]
    bulk_uploads[user_id]['text'] = text
    
    await event.reply(f"Text set to: **{text}**")

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
    
    # New check to ensure name and text are set
    if not bulk_data.get('name') or not bulk_data.get('text'):
        await event.reply("Please set both a name (/bulk_name) and text (/bulk_text) before ending the upload.")
        return

    del bulk_uploads[user_id]
    
    # Send the JSON data to the channel and get the message ID
    json_data = json.dumps(bulk_data)
    bulk_message = await TelegramBot.send_message(entity=Telegram.CHANNEL_ID, message=f'#bulk_files_{json_data}')
    bulk_id = bulk_message.id
    
    bulk_link = f"{Server.BASE_URL}/bulk/{bulk_id}"
    
    await event.reply(
        "Bulk upload complete! Here is your dedicated page:\n\n"
        f"🔗 **Link:** {bulk_link}\n\n"
        "This link is now permanent and will not expire."
    )

@TelegramBot.on(NewMessage(incoming=True, func=filter_files, forwards=False))
@verify_user()
async def channel_file_handler(event: NewMessage.Event | Message):
    secret_code = token_hex(Telegram.SECRET_CODE_LENGTH)
    event.message.text = f"`{secret_code}`"
    message = await send_message(event.message)
    message_id = message.id

    dl_link = f'{Server.BASE_URL}/RD/{message_id}?code={secret_code}'
    tg_link = f"{Server.BASE_URL}/file/{message_id}?code={secret_code}"

    if (event.document and "video" in event.document.mime_type) or event.video:
        try:
            await event.edit(
                buttons=[
                    [Button.url("Download", dl_link)]
                ]
            )
        except (
            MessageAuthorRequiredError,
            MessageIdInvalidError,
            MessageNotModifiedError,
        ):
            pass
    else:
        try:
            await event.edit(
                buttons=[
                    [Button.url("Download", dl_link)]
                ]
            )
        except (
            MessageAuthorRequiredError,
            MessageIdInvalidError,
            MessageNotModifiedError,
        ):
            pass
