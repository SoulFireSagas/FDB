# bot/server/main.py

from quart import Blueprint, Response, request, render_template, redirect
from .error import abort
from bot import TelegramBot
from bot.config import Telegram, Server
from math import ceil, floor
from bot.modules.telegram import get_message, get_file_properties
from secrets import token_hex
import random
from urllib.parse import quote
import json

bp = Blueprint('main', __name__)

@bp.route('/')
async def home():
    return 'api is working'

@bp.route('/RD/<int:file_id>')
async def handle_download_request(file_id):
    code = request.args.get('code') or abort(401)
    
    if Server.USE_BLOGGER_REDIRECT:
        blogger_url = random.choice(Server.BLOGGER_URLS) if Server.BLOGGER_URLS else "https://www.florespick.in"
        final_download_url = f"{Server.BASE_URL}/dl/{file_id}?code={code}"
        redirect_url = f"{blogger_url}?target={quote(final_download_url)}"
        return redirect(redirect_url)
    else:
        return await transmit_file(file_id, code)

@bp.route('/dl/<int:file_id>')
async def transmit_file(file_id, code=None):
    if not code:
        code = request.args.get('code') or abort(401)
    
    file = await get_message(message_id=int(file_id)) or abort(404)
    range_header = request.headers.get('Range', 0)

    if code != file.raw_text:
        abort(403)

    file_name, file_size, mime_type = get_file_properties(file)
    
    if range_header:
        from_bytes, until_bytes = range_header.replace("bytes=", "").split("-")
        from_bytes = int(from_bytes)
        until_bytes = int(until_bytes) if until_bytes else file_size - 1
    else:
        from_bytes = 0
        until_bytes = file_size - 1

    if (until_bytes > file_size) or (from_bytes < 0) or (until_bytes < from_bytes):
        abort(416, 'Invalid range.')

    chunk_size = 1024 * 1024
    until_bytes = min(until_bytes, file_size - 1)

    offset = from_bytes - (from_bytes % chunk_size)
    first_part_cut = from_bytes - offset
    last_part_cut = until_bytes % chunk_size + 1

    req_length = until_bytes - from_bytes + 1
    part_count = ceil(until_bytes / chunk_size) - floor(offset / chunk_size)
    
    headers = {
            "Content-Type": f"{mime_type}",
            "Content-Range": f"bytes {from_bytes}-{until_bytes}/{file_size}",
            "Content-Length": str(req_length),
            "Content-Disposition": f'attachment; filename="{file_name}"',
            "Accept-Ranges": "bytes",
        }

    async def file_generator():
        current_part = 1
        async for chunk in TelegramBot.iter_download(file, offset=offset, chunk_size=chunk_size, stride=chunk_size, file_size=file_size):
            if not chunk:
                break
            elif part_count == 1:
                yield chunk[first_part_cut:last_part_cut]
            elif current_part == 1:
                yield chunk[first_part_cut:]
            elif current_part == part_count:
                yield chunk[:last_part_cut]
            else:
                yield chunk

            current_part += 1

            if current_part > part_count:
                break

    return Response(file_generator(), headers=headers, status=206 if range_header else 200)

@bp.route('/file/<int:file_id>')
async def file_deeplink(file_id):
    code = request.args.get('code') or abort(401)
    return redirect(f'https://t.me/{Telegram.BOT_USERNAME}?start=file_{file_id}_{code}')

# NEW: Route for the bulk file page
@bp.route('/bulk/<int:bulk_id>')
async def bulk_page(bulk_id):
    # Retrieve the message from the channel using the message ID
    bulk_message = await TelegramBot.get_messages(entity=Telegram.CHANNEL_ID, ids=bulk_id) or abort(404)
    
    # Check if the message contains our bulk file data flag
    if not bulk_message.text.startswith('#bulk_files_'):
        abort(404)
        
    # Extract and parse the JSON data
    bulk_data_json = bulk_message.text.replace('#bulk_files_', '', 1)
    bulk_data = json.loads(bulk_data_json)
    
    return await render_template('bulk_page.html', bulk_data=bulk_data)
