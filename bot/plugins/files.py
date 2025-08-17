from telethon import Button
from telethon.events import NewMessage
from telethon.errors import MessageAuthorRequiredError, MessageNotModifiedError, MessageIdInvalidError
from telethon.tl.custom import Message
from secrets import token_hex
from bot import TelegramBot
from bot.config import Telegram, Server
from bot.modules.decorators import verify_user
from bot.modules.telegram import send_message, filter_files
from bot.modules.static import *
from urllib.parse import quote
from math import ceil, floor


@TelegramBot.on(NewMessage(incoming=True, func=filter_files))
@verify_user(private=True)
async def user_file_handler(event: NewMessage.Event | Message):
    secret_code = token_hex(Telegram.SECRET_CODE_LENGTH)
    event.message.text = f'`{secret_code}`'
    message = await send_message(event.message)
    message_id = message.id

    

    dl_link = f'{Server.BASE_URL}/RD/{message_id}?code={secret_code}'
        
    tg_link = f'{Server.BASE_URL}/file/{message_id}?code={secret_code}'
    deep_link = f'https://t.me/{Telegram.BOT_USERNAME}?start=file_{message_id}_{secret_code}'

   

    if (event.document and 'video' in event.document.mime_type) or event.video:
        #stream_link = f'{Server.BASE_URL}/stream/{message_id}?code={secret_code}'
        await event.reply(
            message= MediaLinksText % {'dl_link': dl_link}, #'tg_link': tg_link, 'tg_link': tg_link, 'stream_link': stream_link},
            buttons=[
                [
                    Button.url('Download', dl_link)
                   # Button.url('Stream', stream_link)
                #],
               # [
                 #   Button.url('Get File', deep_link),
                 #   Button.inline('Revoke', f'rm_{message_id}_{secret_code}')
                ]
            ]
        )
    else:
        await event.reply(
            message=FileLinksText % {'dl_link': dl_link}, #'tg_link': tg_link},
            buttons=[
                [
                    Button.url('Download', dl_link)
                #    Button.url('Get File', deep_link)
               # ],
              #  [
                #    Button.inline('Revoke', f'rm_{message_id}_{secret_code}')
                ]
            ]
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
        #stream_link = f"{Server.BASE_URL}/stream/{message_id}?code={secret_code}"

        try:
            await event.edit(
                buttons=[
                    [Button.url("Download", dl_link)]#Button.url("Stream", stream_link)],
                    #[Button.url("Get File", tg_link)],
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
                    [Button.url("Download", dl_link)]#, Button.url("Get File", tg_link)]
                ]
            )
        except (
            MessageAuthorRequiredError,
            MessageIdInvalidError,
            MessageNotModifiedError,
        ):
            pass


bulk_uploads = {}

@TelegramBot.on(NewMessage(incoming=True, pattern='/bulk'))
@verify_user(private=True)
async def start_bulk_upload(event: NewMessage.Event | Message):
    """
    Starts the bulk upload process for a user.
    """
    parts = event.text.split(' ', 2)
    if len(parts) < 3:
        await event.reply("Please use the format: /bulk [name] [text]")
        return
        
    name = parts[1]
    text = parts[2]
    user_id = event.sender_id
    
    bulk_uploads[user_id] = {'name': name, 'text': text, 'files': []}
    
    await event.reply(
        "Bulk upload started. Send me your files. When you're done, use the /bulk_end command."
    )

@TelegramBot.on(NewMessage(incoming=True, func=filter_files))
@verify_user(private=True)
async def handle_user_file_in_bulk(event: NewMessage.Event | Message):
    """
    Handles file uploads and adds them to the bulk list if the user is in bulk mode.
    """
    user_id = event.sender_id
    
    # Check if the user is in bulk upload mode
    if user_id in bulk_uploads:
        file = event.message
        
        if not file.document and not file.video:
            await event.reply("I can only process documents or videos for bulk uploads.")
            return

        file_size = 0
        if file.document:
            file_size = file.document.size
        elif file.video:
            file_size = file.video.size
            
        file_info = {'id': file.id, 'size': file_size}
        bulk_uploads[user_id]['files'].append(file_info)
        
        file_count = len(bulk_uploads[user_id]['files'])
        await event.reply(f"File {file_count} added to bulk list.")
    else:
        # Re-using your original single file handler logic
        secret_code = token_hex(Telegram.SECRET_CODE_LENGTH)
        event.message.text = f'`{secret_code}`'
        message = await send_message(event.message)
        message_id = message.id
        
        dl_link = f'{Server.BASE_URL}/Episodes/{message_id}?code={secret_code}'
            
        await event.reply(
            message=FileLinksText % {'dl_link': dl_link},
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

    # In a real app, you would save this list of files to a database
    # and get a unique bulk_id for it. For this example, we'll just use a random ID.
    bulk_id = token_hex(16)
    
    # Save the bulk data to a temporary storage
    bulk_data = bulk_uploads[user_id]
    del bulk_uploads[user_id] # Clear the user's state
    
    # Store the bulk data globally for the web server to access.
    # A real implementation would use Redis or another database here.
    TelegramBot.bulk_cache[bulk_id] = bulk_data
    
    # Generate the single link to the bulk page
    bulk_link = f"{Server.BASE_URL}/bulk/{bulk_id}"
    
    await event.reply(
        "Bulk upload complete! Here is your dedicated page:\n\n"
        f"🔗 **Link:** {bulk_link}\n\n"
        "This link will expire after a while."
    )





