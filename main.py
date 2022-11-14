import warnings
import sys
import logging
import requests
import pytz
import pandas as pd
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, Bot
from telegram.ext import (
    CommandHandler,
    PollAnswerHandler,
    CallbackQueryHandler,
    ConversationHandler,
    CallbackContext,
    MessageHandler,
    Filters,
    Updater
)
from datetime import datetime, time, timedelta
from gtts import gTTS
from PIL import Image, ImageDraw
from random import randrange
from dotenv import load_dotenv
from io import BytesIO
from utils import database as db
# from utils import contacts_drive as contacts
from src import poll, tareas, birthday, listas, tesoreria, drive, new_member

warnings.filterwarnings("ignore")

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("main")
logging.getLogger('apscheduler').propagate = False
LOQUENDO_1, LOQUENDO_2 = range(2)
ESTADO_UNO, ESTADO_DOS = range(2)

ID_MANITOBA = int(os.environ.get("ID_MANITOBA"))
ID_CONVERSACIONES = int(os.environ.get("ID_CONVERSACIONES"))

ID_TELEGRAM = 777000
load_dotenv()
TOKEN = os.environ.get("TOKEN")
mode = os.environ.get("mode")
print(TOKEN)
print(mode)
if mode == "prod":
    def run(updater):
        updater.start_polling()
        updater.idle()

elif mode == "prod":
    def run(updater):
        PORT = int(os.environ.get("PORT", "8443"))
        HEROKU_APP_NAME = os.environ.get("HEROKU_APP_NAME")
        updater.start_webhook(listen="0.0.0.0", port=8000, url_path=TOKEN,
                              webhook_url="https://web-production-3fc5.up.railway.app/")
else:
    sys.exit()

def echo(update: Update, context: CallbackContext):
    print(f"{update.message.text}")
          
if __name__ == "__main__":
    load_dotenv()
    my_bot = Bot(token=TOKEN)
    updater = Updater(my_bot.token, use_context=True)
    dp = updater.dispatcher

    job = updater.job_queue

    dp.add_handler(MessageHandler(Filters.all, echo))
    pd.options.display.width = 0

    logger.info(f"Iniciando el bot")
    run(updater)
