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

# Temporary in-memory storage for bulk uploads.
# Format: {user_id: {'message_id': ..., 'data': {'name': '', 'text': '', 'files': []}}}
bulk_uploads = {}

async def get_bulk_data(user_id):
    """
    Retrieves a user's bulk data from the temporary channel message.
    """
    if user_id in bulk_uploads:
        temp_message_id = bulk_uploads[user_id]['message_id']
        try:
            bulk_message = await TelegramBot.get_messages(entity=Telegram.CHANNEL_ID, ids=temp_message_id)
            if bulk_message and bulk_message.text.startswith('#temp_bulk_files_'):
                bulk_data_json = bulk_message.text.replace('#temp_bulk_files_', '', 1)
                return json.loads(bulk_data_json)
        except Exception:
            # Handle cases where the message is deleted or not found
            pass
    return None

async def save_bulk_data(user_id, bulk_data):
    """
    Saves a user's bulk data to a temporary channel message.
    """
    json_data = json.dumps(bulk_data)
    
    if user_id in bulk_uploads:
        temp_message_id = bulk_uploads[user_id]['message_id']
        try:
            await TelegramBot.edit_message(
                entity=Telegram.CHANNEL_ID,
                id=temp_message_id,
                text=f'#temp_bulk_files_{json_data}'
            )
            return temp_message_id
        except Exception:
            # If message is not found, we create a new one
            del bulk_uploads[user_id]
            pass

    bulk_message = await TelegramBot.send_message(entity=Telegram.CHANNEL_ID, message=f'#temp_bulk_files_{json_data}')
    bulk_uploads[user_id] = {'message_id': bulk_message.id, 'data': bulk_data}
    return bulk_message.id


@TelegramBot.on(NewMessage(incoming=True, pattern='/bulk'))
@verify_user(private=True)
async def start_bulk_upload(event: NewMessage.Event | Message):
    """
    Starts the bulk upload process for a user.
    """
    user_id = event.sender_id
    
    # Initialize the bulk_uploads dictionary for the user with empty values
    bulk_data = {'name': '', 'text': '', 'files': []}
    await save_bulk_data(user_id, bulk_data)
    
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
    
    bulk_data = await get_bulk_data(user_id)
    if not bulk_data:
        await event.reply("Please start a bulk upload first with the /bulk command.")
        return
    
    if len(parts) < 2:
        await event.reply("Please provide a name. Example: /bulk_name My Awesome File Collection")
        return
        
    name = parts[1]
    bulk_data['name'] = name
    await save_bulk_data(user_id, bulk_data)
    
    await event.reply(f"Name set to: **{name}**")

@TelegramBot.on(NewMessage(incoming=True, pattern='/bulk_text'))
@verify_user(private=True)
async def set_bulk_text(event: NewMessage.Event | Message):
    """
    Sets the text for the bulk upload.
    """
    user_id = event.sender_id
    parts = event.text.split(' ', 1)
    
    bulk_data = await get_bulk_data(user_id)
    if not bulk_data:
        await event.reply("Please start a bulk upload first with the /bulk command.")
        return
        
    if len(parts) < 2:
        await event.reply("Please provide text. Example: /bulk_text My File Text")
        return
        
    text = parts[1]
    bulk_data['text'] = text
    await save_bulk_data(user_id, bulk_data)
    
    await event.reply(f"Text set to: **{text}**")

@TelegramBot.on(NewMessage(incoming=True, func=filter_files))
@verify_user(private=True)
async def user_file_handler(event: NewMessage.Event | Message):
    """
    Handles user file uploads and either adds them to the bulk list or
    creates a single-file link.
    """
    user_id = event.sender_id
    
    bulk_data = await get_bulk_data(user_id)
    
    # Check if the user is in bulk upload mode
    if bulk_data:
        file = event.message
        
        # Generate and save the secret code for each file
        secret_code = token_hex(Telegram.SECRET_CODE_LENGTH)
        file.text = f'`{secret_code}`'
        message = await send_message(file)
        
        # Get file properties from the new message object
        file_name, file_size, mime_type = get_file_properties(message)
        
        file_info = {'id': message.id, 'size': file_size, 'secret_code': secret_code}
        bulk_data['files'].append(file_info)
        await save_bulk_data(user_id, bulk_data)
        
        file_count = len(bulk_data['files'])
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
    
    bulk_data = await get_bulk_data(user_id)
    
    if not bulk_data or not bulk_data['files']:
        await event.reply("No files were uploaded. Please use /bulk to start.")
        return
        
    # Check to ensure name and text are set
    if not bulk_data.get('name') or not bulk_data.get('text'):
        await event.reply("Please set both a name (/bulk_name) and text (/bulk_text) before ending the upload.")
        return

    # Send the JSON data to the channel and get the message ID
    json_data = json.dumps(bulk_data)
    
    # Send the final, persistent message and get its ID
    bulk_message = await TelegramBot.send_message(entity=Telegram.CHANNEL_ID, message=f'#bulk_files_{json_data}')
    bulk_id = bulk_message.id
    
    # Delete the temporary message from the channel to clean up
    temp_message_id = bulk_uploads[user_id]['message_id']
    await TelegramBot.delete_messages(entity=Telegram.CHANNEL_ID, ids=temp_message_id)
    del bulk_uploads[user_id]
    
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
