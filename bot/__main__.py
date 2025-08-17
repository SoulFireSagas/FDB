# bot/__init__.py
from importlib import import_module
from pathlib import Path
from telethon import TelegramClient
from telethon.tl.custom import Button
from bot.config import Telegram
from bot.server import server

# A placeholder for a simple logger. In a real application, you would import a proper logger.
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class TelegramBot(TelegramClient):
    """
    A custom class for our Telegram bot client.
    This is where we'll store shared resources like the bulk file cache.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # This is the new dictionary to temporarily store bulk upload data
        # A more robust solution would use a persistent database like Redis.
        self.bulk_cache = {}

def load_plugins():
    count = 0
    for path in Path('bot/plugins').rglob('*.py'):
        import_module(f'bot.plugins.{path.stem}')
        count += 1
    logger.info(f'Loaded {count} {"plugins" if count > 1 else "plugin"}.')

if __name__ == '__main__':
    logger.info('initializing...')
    TelegramBot.loop.create_task(server.serve())
    TelegramBot.start(bot_token=Telegram.BOT_TOKEN)
    logger.info('Telegram client is now started.')
    logger.info('Loading bot plugins...')
    load_plugins()
    logger.info('Bot is now ready!')
    TelegramBot.run_until_disconnected()
