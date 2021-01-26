from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, Bot
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    CallbackContext,
    MessageHandler,
    Filters,
    Updater
)
from datetime import datetime, time
from gtts import gTTS
from PIL import Image, ImageDraw
import pandas as pd
from dotenv import load_dotenv
import random
import os
import sys
import logging
import requests
from io import BytesIO

import database as db
import listas
import tareas
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger()

LOQUENDO_1, LOQUENDO_2 = range(2)
CULOS_1 = range(1)

ID_MANITOBA = -1001255856526
ID_CONVERSACIONES = -1001462256012
ID_TELEGRAM = 777000

load_dotenv()
TOKEN = os.environ.get("TOKEN")
mode = os.environ.get("mode")

if mode == "dev":
    def run(updater):
        updater.start_polling()
        updater.idle()

elif mode == "prod":
    def run(updater):
        PORT = int(os.environ.get("PORT", "8443"))
        HEROKU_APP_NAME = os.environ.get("HEROKU_APP_NAME")

        updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN)
        updater.bot.set_webhook(f"https://{HEROKU_APP_NAME}.herokuapp.com/{TOKEN}")
else:
    sys.exit()


def end(update: Update, context: CallbackContext):
    logger.info("PersonaEnd", update.message.text)
    query = update.callback_query
    query.answer()
    query.edit_message_text(text="See you next time!")
    return ConversationHandler.END


def random_number(update: Update, context: CallbackContext):
    user_id = update.effective_user['id']
    logger.info(f"El usuario {user_id} ha solicitado un numero aleatorio")
    number = random.randint(0, 10)
    context.bot.sendMessage(chat_id=user_id, parse_mode="HTML", text=f"<b>Numero</b> aleatorio:\n{number}")


def birthday(context: CallbackContext):
    data = db.select("data")
    fecha = datetime.today().strftime('%d/%m')
    cumpleaneros = data[data.cumple == fecha]

    for _, cumpleanero in cumpleaneros.iterrows():
        print(f"Felicidades {cumpleanero.nombre}")
        context.bot.sendMessage(chat_id=ID_MANITOBA, parse_mode="HTML",
                                text=f"Felicidades <b>{cumpleanero.nombre}</b>")


def echo(update: Update, context: CallbackContext):
    data = db.select("data")
    user_id = int(update.effective_user.id)
    chat_id = int(update.effective_chat.id)
    conversacion_id = int(update.message.message_id)
    if chat_id == ID_CONVERSACIONES:
        conversaciones = db.select("conversaciones")
        if user_id == ID_TELEGRAM:
            mensaje = context.bot.sendMessage(chat_id=ID_MANITOBA, parse_mode="HTML",
                                              text=f"Se ha iniciado una conversacion: <b>{update.message.text}</b>")
            db.insert_conversacion(conversacion_id, mensaje.message_id, update.message.text)
        else:
            reply_id = update.message.reply_to_message.message_id
            conversacion = conversaciones[conversaciones.id == reply_id].iloc[0]
            conversacion.total_mensajes += 1
            db.update_conversacion(conversacion)
            context.bot.deleteMessage(chat_id=ID_MANITOBA, message_id=int(conversacion.mensaje_id))
            mensaje = context.bot.sendMessage(chat_id=ID_MANITOBA, parse_mode="HTML",
                                          text=f"La conversación <b>{conversacion.nombre}</b> tiene un total de {conversacion.total_mensajes} mensajes")
            conversacion.mensaje_id=mensaje.message_id
            db.update_conversacion(conversacion)
    nombre = update.effective_user.first_name
    fila = data.loc[data.id == user_id]
    data.loc[data.id == user_id, "ultimo_mensaje"] = datetime.today().strftime('%d/%m/%Y %H:%M')
    if len(fila) == 1:
        fila = fila.iloc[0]
        fila.total_mensajes += 1
        fila.ultimo_mensaje = datetime.today().strftime('%d/%m/%Y %H:%M')
        db.update_data(fila)
        logger.info(
            f"{fila.apodo} ha enviado {update.message.text}. Con un total de {fila.total_mensajes} mensajes")
    else:
        logger.info(f"{nombre} con id: {user_id} ha enviado {update.message.text}")



def loquendo(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    user = update.effective_user
    logger.info(f"User {user.first_name} entro en el comando loquendo")
    # Send message with text and appended InlineKeyboard
    context.bot.deleteMessage(update.message.chat_id, update.message.message_id)
    context.user_data["oldMessage"] = context.bot.sendMessage(chat_id, "¿Qué texto quieres convertir?")
    # Tell ConversationHandler that we're in state `FIRST` now
    return LOQUENDO_1


def loquendo2(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    user = update.effective_user
    idi = ['af', 'ar', 'bn', 'bs', 'ca', 'cs', 'cy', 'da', 'de', 'el', 'en', 'eo', 'es', 'et', 'fi', 'fr', 'gu',
           'hi', 'hr', 'hu', 'hy', 'id', 'is', 'it', 'ja', 'jw', 'km', 'kn', 'ko', 'la', 'lv', 'mk', 'ml', 'mr',
           'my', 'ne', 'nl', 'no', 'pl', 'pt', 'ro', 'ru', 'si', 'sk', 'sq', 'sr', 'su', 'sv', 'sw', 'ta', 'te',
           'th', 'tl', 'tr', 'uk', 'ur', 'vi', 'zh-CN', 'zh-cn', 'zh-tw', 'en-us', 'en-ca', 'en-uk', 'en-gb',
           'en-au', 'en-gh', 'en-in', 'en-ie', 'en-nz', 'en-ng', 'en-ph', 'en-za', 'en-tz', 'fr-ca', 'fr-fr',
           'pt-br', 'pt-pt', 'es-es', 'es-us', ]
    idiomas = ['Afrikaans', 'Arabic', 'Bengali', 'Bosnian', 'Catalan', 'Czech', 'Welsh', 'Danish', 'German', 'Greek',
               'English', 'Esperanto', 'Spanish', 'Estonian', 'Finnish', 'French', 'Gujarati', 'Hindi', 'Croatian',
               'Hungarian', 'Armenian', 'Indonesian', 'Icelandic', 'Italian', 'Japanese', 'Javanese', 'Khmer',
               'Kannada',
               'Korean', 'Latin', 'Latvian', 'Macedonian', 'Malayalam', 'Marathi', 'Myanmar', 'Nepali', 'Dutch',
               'Norwegian', 'Polish', 'Portuguese', 'Romanian', 'Russian', 'Sinhala', 'Slovak', 'Albanian', 'Serbian',
               'Sundanese', 'Swedish', 'Swahili', 'Tamil', 'Telugu', 'Thai', 'Filipino', 'Turkish', 'Ukrainian', 'Urdu',
               'Vietnamese', 'Chinese', 'Mandarin Ch', 'Mandarin Tw', '(US)',
               '(Canada)', '(UK)', '(UK)', '(Australia)', '(Ghana)',
               '(India)', 'English (Ireland)', 'English (New Zealand)', 'English (Nigeria)',
               '(Philippines)', '(South Africa)', '(Tanzania)', 'French CAN',
               'French', 'Portuguese Br', 'Portuguese Pt', 'Español',
               'Spanish USA', ]
    part_keyboard = []
    keyboard = []
    for i, (lang, lg) in enumerate(zip(idiomas, idi)):
        part_keyboard.append(InlineKeyboardButton(lang, callback_data=lg))
        if i % 3 == 2 or i == len(idiomas):
            keyboard.append(part_keyboard)
            part_keyboard = []

    reply_markup = InlineKeyboardMarkup(keyboard)
    logger.info(f"User {user.first_name} mando el texto:\n {update.message.text}")
    # Send message with text and appended InlineKeyboard
    context.bot.deleteMessage(context.user_data["oldMessage"].chat_id, context.user_data["oldMessage"].message_id)
    context.user_data["oldMessage"] = context.bot.sendMessage(chat_id, text="¿Qué idioma quieres poner?",
                                                              reply_markup=reply_markup)

    context.user_data["texto"] = update.message.text
    # Tell ConversationHandler that we're in state `FIRST` now
    return LOQUENDO_2


def end_loquendo(update: Update, context: CallbackContext):
    chat_id = update.callback_query.message.chat_id
    user = update.effective_user
    logger.info(f"User {user.first_name} mando el idioma:\n {update.callback_query.data}")
    # Send message with text and appended InlineKeyboard
    context.bot.deleteMessage(context.user_data["oldMessage"].chat_id, context.user_data["oldMessage"].message_id)
    tts = gTTS(context.user_data["texto"], lang=update.callback_query.data)
    tts.save("audio.mp3")
    context.bot.sendAudio(chat_id, audio=open("audio.mp3", "rb"))

    # Tell ConversationHandler that we're in state `FIRST` now
    return ConversationHandler.END


def check(update: Update, context: CallbackContext):
    context.bot.sendMessage(chat_id=2, text="Estoy probando cosas, os van a llegar un par")


def culos(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    user = update.effective_user
    logger.info(f"User {user.first_name} entro en el comando culos")
    # Send message with text and appended InlineKeyboard
    context.user_data["oldMessage"] = context.bot.sendMessage(chat_id, "Enviame la imagen sin bordes")
    context.bot.deleteMessage(update.message.chat_id, update.message.message_id)
    # Tell ConversationHandler that we're in state `FIRST` now
    return CULOS_1


def culos2(update: Update, context: CallbackContext):
    # im1 = Image.open('mono.jpg')
    # url = context.bot.get_file(file_id=update.message.photo[-1].file_id).file_path
    # response = requests.get(url)
    # im2 = Image.open(BytesIO(response.content))
    # size = 150, 150
    # im2.thumbnail(size, Image.ANTIALIAS)
    # x, y = im2.size
    # eX, eY = 90, 130  # Size of Bounding Box for ellipse
    # bbox = (x / 2 - eX / 2, y / 2 - eY / 2, x / 2 + eX / 2, y / 2 + eY / 2)
    #
    # mask_im = Image.new("L", im2.size, 0)
    # draw = ImageDraw.Draw(mask_im)
    # draw.ellipse(bbox, fill=255)
    # back_im = im1.copy()
    # back_im.paste(im2, (260, 350), mask_im)
    # back_im.save('culo_final.jpg', quality=95)

    im1 = Image.open('mono.jpg')
    url = context.bot.get_file(file_id=update.message.photo[-1].file_id).file_path
    response = requests.get(url)
    im2 = Image.open(BytesIO(response.content))
    size = 160, 160
    im2.thumbnail(size, Image.ANTIALIAS)
    x, y = im2.size
    eX, eY = 80, 120  # Size of Bounding Box for ellipse
    bbox = (x / 2 - eX / 2, y / 2 - eY / 2, x / 2 + eX / 2, y / 2 + eY / 2)

    mask_im = Image.new("L", im2.size, 0)
    draw = ImageDraw.Draw(mask_im)
    draw.ellipse(bbox, fill=255)

    back_im = im1.copy()
    back_im.paste(im2, (680, 90), mask_im)
    back_im.show()
    back_im.save('culo_final.jpg', quality=95)

    chat_id = update.message.chat_id
    user = update.effective_user
    logger.info(f"User {user.first_name} mando el idioma:\n {update.message.text}")
    # Send message with text and appended InlineKeyboard
    context.bot.deleteMessage(context.user_data["oldMessage"].chat_id, context.user_data["oldMessage"].message_id)
    context.bot.deleteMessage(update.message.chat_id, update.message.message_id)
    context.bot.sendPhoto(chat_id, photo=open("culo_final.jpg", "rb"))

    # Tell ConversationHandler that we're in state `FIRST` now
    return ConversationHandler.END


if __name__ == "__main__":
    load_dotenv()
    my_bot = Bot(token=TOKEN)
    # print(my_bot.getMe())
    updater = Updater(my_bot.token, use_context=True)

    dp = updater.dispatcher

    job = updater.job_queue

    pd.options.display.width = 0

    conv_handler_loquendo = ConversationHandler(
        entry_points=[CommandHandler('loquendo', loquendo)],
        states={
            LOQUENDO_1: [MessageHandler(Filters.text & ~Filters.command, loquendo2)],
            LOQUENDO_2: [CallbackQueryHandler(end_loquendo)]

        },
        fallbacks=[CommandHandler('loquendo', loquendo)],
    )
    conv_handler_culos = ConversationHandler(
        entry_points=[CommandHandler('culos', culos)],
        states={
            CULOS_1: [MessageHandler(Filters.photo & ~Filters.command, culos2)]

        },
        fallbacks=[CommandHandler('culos', culos)],
    )

    dp.add_handler(listas.conv_handler_listas)
    dp.add_handler(conv_handler_loquendo)
    dp.add_handler(conv_handler_culos)
    dp.add_handler(tareas.conv_handler_tareas)
    dp.add_handler(CommandHandler("check", check))

    dp.add_handler(CommandHandler("random", random_number))
    dp.add_handler(MessageHandler(Filters.all, echo))

    job.run_daily(birthday, time(6, 0, 00, 000000), days=(0, 1, 2, 3, 4, 5, 6))
    run(updater)
