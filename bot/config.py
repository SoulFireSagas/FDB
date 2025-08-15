from os import environ as env



class Telegram:

    API_ID = int(env.get("TELEGRAM_API_ID", 22928570))

    API_HASH = env.get("TELEGRAM_API_HASH", "60bb37bddecb48c27c3e86906a077603")

    OWNER_ID = int(env.get("OWNER_ID", 2010016480))

    ALLOWED_USER_IDS = env.get("ALLOWED_USER_IDS", "2010016480").split()

    BOT_USERNAME = env.get("TELEGRAM_BOT_USERNAME", "FPDL_1Robot")

    BOT_TOKEN = env.get("TELEGRAM_BOT_TOKEN", "8450788394:AAGPcBSKFLLBnD4ED_Lxk2piHcJ-6iF5dgg")

    CHANNEL_ID = int(env.get("TELEGRAM_CHANNEL_ID", -1002744991028))

    SECRET_CODE_LENGTH = int(env.get("SECRET_CODE_LENGTH", 12))



class Server:

    BASE_URL = env.get("BASE_URL", "https://fond-marnia-soulfiresagas-e0ac340f.koyeb.app")

    BIND_ADDRESS = env.get("BIND_ADDRESS", "0.0.0.0")

    PORT = int(env.get("PORT", 8080))



    USE_BLOGGER_REDIRECT = True  # Set False to disable

    BLOGGER_URL = "https://redirectarc.blogspot.com/2025/08/redirect.html"

    DOWNLOAD_DELAY_SECONDS = 7  # Countdown duration



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















