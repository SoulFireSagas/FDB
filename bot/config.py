from os import environ as env



class Telegram:

    API_ID = int(env.get("TELEGRAM_API_ID", ))
    API_HASH = env.get("TELEGRAM_API_HASH", "")
    OWNER_ID = int(env.get("OWNER_ID", ))
    ALLOWED_USER_IDS = env.get("ALLOWED_USER_IDS", "").split()
    BOT_USERNAME = env.get("TELEGRAM_BOT_USERNAME", "")
    BOT_TOKEN = env.get("TELEGRAM_BOT_TOKEN", "")
    CHANNEL_ID = int(env.get("TELEGRAM_CHANNEL_ID", ))
    SECRET_CODE_LENGTH = int(env.get("SECRET_CODE_LENGTH", 12))



class Server:

    BASE_URL = env.get("BASE_URL", "")
    BIND_ADDRESS = env.get("BIND_ADDRESS", "0.0.0.0")
    PORT = int(env.get("PORT", 8080))



    USE_BLOGGER_REDIRECT = True  # Set False to disable
    # Corrected: This should be a list of the actual Blogger redirect URLs.
    BLOGGER_URLS = env.get("BLOGGER_URLS", "").split(',')
    # This is the final download link that the Blogger page will use
    # It should be your server's /dl/ endpoint
    RD_URL = env.get("RD_URL", f"{BASE_URL}/RD")



# LOGGING CONFIGURATION

LOGGER_CONFIG_JSON = {

    'version': 1,

    'formatters': {

        'default': {

            'format': '[%(asctime)s][%(name)s][%(levelname)s] -> %(message)s',

            'datefmt': '%d/%m/%Y %H:%M:%S'

        },

    },

    'handlers': {

        'file_handler': {

            'class': 'logging.FileHandler',

            'filename': 'event-log.txt',

            'formatter': 'default'

        },

        'stream_handler': {

            'class': 'logging.StreamHandler',

            'formatter': 'default'

        }

    },

    'loggers': {

        'uvicorn': {

            'level': 'INFO',

            'handlers': ['file_handler', 'stream_handler']

        },

        'uvicorn.error': {

            'level': 'WARNING',

            'handlers': ['file_handler', 'stream_handler']

        },

        'bot': {

            'level': 'INFO',

            'handlers': ['file_handler', 'stream_handler']

        }

    }

}
























