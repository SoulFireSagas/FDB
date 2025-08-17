# bot/__init__.py
from telethon import TelegramClient
from logging import getLogger
from logging.config import dictConfig
from .config import Telegram, LOGGER_CONFIG_JSON

dictConfig(LOGGER_CONFIG_JSON)

version = 1.5
logger = getLogger('bot')

# Define the custom TelegramBot class with the bulk_cache attribute
class TelegramBot(TelegramClient):
    """
    A custom class for our Telegram bot client.
    This is where we'll store shared resources like the bulk file cache.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # This is the new dictionary to temporarily store bulk upload data
        self.bulk_cache = {}

# Now, create an instance of our custom TelegramBot class
TelegramBot = TelegramBot(
    session='bot',
    api_id=Telegram.API_ID,
    api_hash=Telegram.API_HASH
)
