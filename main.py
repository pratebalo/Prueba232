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
import utils.client_drive as client_drive

import pandas as pd
from dotenv import load_dotenv
import sys
import logging
import requests
import pytz
from io import BytesIO

from utils import database as db
import os
from src import poll, tareas, birthday, listas, tesoreria, drive

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("main")

LOQUENDO_1, LOQUENDO_2 = range(2)
ESTADO_UNICO = range(1)

ID_MANITOBA = int(os.environ.get("ID_MANITOBA"))
ID_CONVERSACIONES = int(os.environ.get("ID_CONVERSACIONES"))

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

        updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN,
                              webhook_url=f"https://{HEROKU_APP_NAME}.herokuapp.com/{TOKEN}")
else:
    sys.exit()


def muditos(context: CallbackContext):
    data = db.select("data")
    hoy = datetime.today()
    data.ultimo_mensaje = pd.to_datetime(data.ultimo_mensaje)
    for _, persona in data[data.ultimo_mensaje < (hoy - timedelta(23))].iterrows():
        context.bot.sendMessage(ID_MANITOBA, parse_mode="HTML",
                                text=f"""Te echamos de menos <a href="tg://user?id={persona.id}">{persona.apodo}</a>""")


def echo(update: Update, context: CallbackContext):
    data = db.select("data")
    user_id = int(update.effective_user.id)
    chat_id = int(update.effective_chat.id)
    if chat_id == ID_CONVERSACIONES:
        conversaciones = db.select("conversaciones")
        if user_id == ID_TELEGRAM:
            if update.message.text:
                texto = update.message.text
            elif update.message.poll:
                texto = update.message.poll.question
            else:
                texto = "Nueva conversación"
            mensaje = context.bot.sendMessage(chat_id=ID_MANITOBA, parse_mode="HTML",
                                              text=f"Se ha iniciado una conversacion: <a f='https://t.me/c/1462256012/{update.message.message_id}?thread={update.message.message_id}'>{texto}</a>")
            db.insert_conversacion(update.message.message_id, mensaje.message_id, texto)
        else:
            reply_id = update.message.reply_to_message.message_id
            conversacion = conversaciones[conversaciones.id == reply_id].iloc[0]
            conversacion.total_mensajes += 1
            db.update_conversacion(conversacion)
            try:
                context.bot.deleteMessage(chat_id=ID_MANITOBA, message_id=int(conversacion.mensaje_id))
            except:
                print("Mensaje eliminado")

            mensaje = context.bot.sendMessage(chat_id=ID_MANITOBA, parse_mode="HTML",
                                              text=f"La conversacion <a href='https://t.me/c/1462256012/{conversacion.id}?thread={conversacion.id}'>{conversacion.nombre}</a> tiene un total de {conversacion.total_mensajes} mensajes")

            conversacion.mensaje_id = mensaje.message_id
            db.update_conversacion(conversacion)
    nombre = update.effective_user.first_name
    fila = data.loc[data.id == user_id]
    if len(fila) == 1:
        fila = fila.iloc[0]
        fila.total_mensajes += 1
        fila.ultimo_mensaje = datetime.today().strftime('%d/%m/%Y %H:%M:S')
        if update.message:
            if update.message.text:
                logger.info(
                    f"{update.effective_chat.type} -> {fila.apodo} ha enviado {update.message.text}. Con un total de {fila.total_mensajes} mensajes")
            elif update.message.sticker:
                fila.sticker += 1
                logger.info(
                    f"{update.effective_chat.type} -> {fila.apodo} ha enviado el sticker {update.message.sticker.emoji}. Con un total de {fila.total_mensajes} mensajes")
            elif update.message.photo:
                logger.info(
                    f"{update.effective_chat.type} -> {fila.apodo} ha enviado una foto. Con un total de {fila.total_mensajes} mensajes")
            elif update.message.animation:
                fila.gif += 1
                logger.info(
                    f"{update.effective_chat.type} -> {fila.apodo} ha enviado un gif. Con un total de {fila.total_mensajes} mensajes")
            elif update.message.document:
                # doc = update.message.document
                # if "acta" in doc.file_name.lower() and (doc.mime_type == 'application/msword' or doc.mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'):
                #     file = context.bot.get_file(doc.file_id)
                #     file.download(doc.file_name)
                #     path = os.path.dirname(os.path.realpath(__file__))
                #     file_name = doc.file_name.replace(".docx", ".pdf").replace(".doc", ".pdf")
                #     in_file = path + f"/{doc.file_name}"
                #     out_file = path + f"/{file_name}"
                #
                #     word = client.DispatchEx('Word.Application')
                #     doc = word.Documents.Open(in_file)
                #     print(out_file)
                #     doc.SaveAs(out_file, FileFormat=17)
                #     doc.Close()
                #     with open(file_name, "rb") as file:
                #         context.bot.sendDocument(update.effective_chat.id, file)
                #     client_drive.upload_file(file_name,parent_id='1V34ehU4iaHgadWCRSl9hlvZUIn62qWSM')
                #     client_drive.upload_file(doc.file_name,parent_id='1V34ehU4iaHgadWCRSl9hlvZUIn62qWSM')
                logger.info(
                    f"{update.effective_chat.type} -> {fila.apodo} ha enviado el documento {update.message.document.file_name} tipo "
                    f"{update.message.document.mime_type}. Con un total de {fila.total_mensajes} mensajes")
            elif update.message.new_chat_members:
                logger.info(
                    f"{update.effective_chat.type} -> {update.message.new_chat_members} ha entrado al grupo ")
            else:
                logger.info(f"{update.effective_chat.type} -> update.message desconocido:  {update.message}")
            db.update_data(fila)
        elif update.edited_message:
            logger.warning(
                f"{update.effective_chat.type} -> {fila.apodo} ha editado el mensaje por {update.edited_message.text}. Con un total de {fila.total_mensajes} mensajes")
        else:
            logger.info(f"{update.effective_chat.type} ->update desconocido: {update}")

    else:
        logger.info(f"{update.effective_chat.type} -> {nombre} con id: {user_id} ha enviado {update.message.text}")


def loquendo(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    user = update.effective_user
    logger.warning(f"{update.effective_chat.type} -> User {user.first_name} entro en el comando loquendo")
    # Send message with text and appended InlineKeyboard
    context.bot.deleteMessage(update.message.chat_id, update.message.message_id)
    context.user_data["oldMessage"] = \
        context.bot.sendMessage(chat_id, f"{update.effective_user.first_name}: ¿Qué texto quieres convertir?")
    # Tell ConversationHandler that we're in state `FIRST` now
    return LOQUENDO_1


def loquendo2(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    user = update.effective_user
    idi = ['af', 'ar', 'bn', 'bs', 'ca', 'cs', 'cy', 'da', 'de', 'el', 'en', 'eo', 'es', 'et', 'fi', 'fr', 'gu',
           'hi', 'hr', 'hu', 'hy', 'id', 'is', 'it', 'ja', 'jw', 'km', 'kn', 'ko', 'la', 'lv', 'mk', 'ml', 'mr',
           'my', 'ne', 'nl', 'no', 'pl', 'pt', 'ro', 'ru', 'si', 'sk', 'sq', 'sr', 'su', 'sv', 'sw', 'ta', 'te',
           'th', 'tl', 'tr', 'uk', 'ur', 'vi']
    idiomas = ['Afrikaans', 'Arabic', 'Bengali', 'Bosnian', 'Catalan', 'Czech', 'Welsh', 'Danish', 'German', 'Greek',
               'English', 'Esperanto', 'Spanish', 'Estonian', 'Finnish', 'French', 'Gujarati', 'Hindi', 'Croatian',
               'Hungarian', 'Armenian', 'Indonesian', 'Icelandic', 'Italian', 'Japanese', 'Javanese', 'Khmer',
               'Kannada', 'Korean', 'Latin', 'Latvian', 'Macedonian', 'Malayalam', 'Marathi', 'Myanmar', 'Nepali',
               'Dutch', 'Norwegian', 'Polish', 'Portuguese', 'Romanian', 'Russian', 'Sinhala', 'Slovak', 'Albanian',
               'Serbian', 'Sundanese', 'Swedish', 'Swahili', 'Tamil', 'Telugu', 'Thai', 'Filipino', 'Turkish',
               'Ukrainian', 'Urdu', 'Vietnamese']
    part_keyboard = []
    keyboard = []
    for i, (lang, lg) in enumerate(zip(idiomas, idi)):
        part_keyboard.append(InlineKeyboardButton(lang, callback_data=lg))
        if i % 3 == 2 or i == len(idiomas):
            keyboard.append(part_keyboard)
            part_keyboard = []

    reply_markup = InlineKeyboardMarkup(keyboard)
    logger.warning(f"{update.effective_chat.type} -> User {user.first_name} mando el texto:\n {update.message.text}")
    # Send message with text and appended InlineKeyboard
    context.bot.deleteMessage(context.user_data["oldMessage"].chat_id, context.user_data["oldMessage"].message_id)
    context.bot.deleteMessage(update.effective_chat.id, update.message.message_id)
    context.user_data["oldMessage"] = context.bot.sendMessage(chat_id,
                                                              text=f"{update.effective_user.first_name}: ¿Qué idioma quieres poner?",
                                                              reply_markup=reply_markup)

    context.user_data["texto"] = update.message.text
    # Tell ConversationHandler that we're in state `FIRST` now
    return LOQUENDO_2


def end_loquendo(update: Update, context: CallbackContext):
    chat_id = update.callback_query.message.chat_id
    user = update.effective_user
    logger.warning(
        f"{update.effective_chat.type} -> User {user.first_name} mando el idioma:\n {update.callback_query.data}")
    # Send message with text and appended InlineKeyboard
    context.bot.deleteMessage(context.user_data["oldMessage"].chat_id, context.user_data["oldMessage"].message_id)
    tts = gTTS(context.user_data["texto"], lang=update.callback_query.data)
    file_name = "Mensajito de Baden Powell.mp3"
    tts.save(file_name)
    context.bot.sendAudio(chat_id, timeout=60, audio=open(file_name, "rb"))

    # Tell ConversationHandler that we're in state `FIRST` now
    return ConversationHandler.END


def culos(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    user = update.effective_user
    logger.warning(f"{update.effective_chat.type} -> User {user.first_name} entro en el comando culos")
    # Send message with text and appended InlineKeyboard
    context.user_data["oldMessage"] = context.bot.sendMessage(chat_id,
                                                              f"{update.effective_user.first_name}: Enviame una imagen cuadrada de una cara sin bordes")
    context.bot.deleteMessage(update.message.chat_id, update.message.message_id)
    # Tell ConversationHandler that we're in state `FIRST` now
    return ESTADO_UNICO


def culos2(update: Update, context: CallbackContext):
    im1 = Image.open('mono.jpg')
    url = context.bot.get_file(file_id=update.message.photo[-1].file_id).file_path
    response = requests.get(url)
    im2 = Image.open(BytesIO(response.content))
    size = 150, 150
    im2.thumbnail(size, Image.ANTIALIAS)
    x, y = im2.size
    eX, eY = 90, 130  # Size of Bounding Box for ellipse
    bbox = (x / 2 - eX / 2, y / 2 - eY / 2, x / 2 + eX / 2, y / 2 + eY / 2)

    mask_im = Image.new("L", im2.size, 0)
    draw = ImageDraw.Draw(mask_im)
    draw.ellipse(bbox, fill=255)
    back_im = im1.copy()
    back_im.paste(im2, (260, 350), mask_im)
    back_im.save('culo_final.jpg', quality=95)

    # im1 = Image.open('mono.jpg')
    # url = context.bot.get_file(file_id=update.message.photo[-1].file_id).file_path
    # response = requests.get(url)
    # im2 = Image.open(BytesIO(response.content))
    # size = 160, 160
    # im2.thumbnail(size, Image.ANTIALIAS)
    # x, y = im2.size
    # eX, eY = 80, 120  # Size of Bounding Box for ellipse
    # bbox = (x / 2 - eX / 2, y / 2 - eY / 2, x / 2 + eX / 2, y / 2 + eY / 2)
    #
    # mask_im = Image.new("L", im2.size, 0)
    # draw = ImageDraw.Draw(mask_im)
    # draw.ellipse(bbox, fill=255)
    #
    # back_im = im1.copy()
    # back_im.paste(im2, (680, 90), mask_im)
    # back_im.show()
    # back_im.save('culo_final.jpg', quality=95)

    chat_id = update.message.chat_id
    user = update.effective_user
    logger.warning(f"{update.effective_chat.type} -> User {user.first_name} mando la foto")
    # Send message with text and appended InlineKeyboard
    context.bot.deleteMessage(context.user_data["oldMessage"].chat_id, context.user_data["oldMessage"].message_id)
    context.bot.deleteMessage(update.message.chat_id, update.message.message_id)
    context.bot.sendPhoto(chat_id, photo=open("culo_final.jpg", "rb"))

    # Tell ConversationHandler that we're in state `FIRST` now
    return ConversationHandler.END


def pietrobot(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    context.bot.deleteMessage(chat_id, update.message.message_id)
    logger.warning(f"{update.effective_chat.type} -> {update.effective_user.first_name} ha entrado en pietrobot")
    if not chat_id == ID_MANITOBA:
        context.bot.sendMessage(chat_id, text="¿Qué texto quieres enviar?\nMe ha parecido oir que...")
        return ESTADO_UNICO
    else:
        return ConversationHandler.END


def end_pietrobot(update: Update, context: CallbackContext):
    logger.warning(
        f"{update.effective_chat.type} -> {update.effective_user.first_name} ha escrito {update.message.text}")
    context.bot.sendMessage(ID_MANITOBA, text="Me ha parecido oir que " + update.message.text)
    return ConversationHandler.END


def start(update: Update, context: CallbackContext):
    data = db.select("data")
    user_id = int(update.effective_user.id)
    chat_id = int(update.effective_chat.id)

    nombre = update.effective_user.first_name
    fila = data.loc[data.id == user_id]
    if len(fila) == 1:
        fila = fila.iloc[0]
        logger.info(f"{update.effective_chat.type} -> {fila.apodo} ha iniciado el bot")
        context.bot.sendMessage(chat_id,
                                f"Bienvenido {fila.apodo}\nPuedes probar a usar los comandos poniendo / seguido del nombre del comando")
    else:
        logger.info(f"{update.effective_chat.type} -> {nombre} con id: {user_id} ha iniciado el bot")
        context.bot.sendMessage(chat_id,
                                f"Bienvenido {nombre}\nPuedes probar a usar los comandos poniendo / seguido del nombre del comando")

    context.bot.sendMessage(chat_id, "Los comandos son:\n"
                                     "  ·listas - Crea, edita o borra una lista\n"
                                     "  ·tareas - Crea, edita o borra una tarea\n"
                                     "  ·loquendo - Envíame un texto y te reenvío un audio\n"
                                     "  ·tesoreria - Tesorería\n"
                                     "  ·pietrobot -  Envíame un mensaje por privado y lo envío por el grupo\n"
                                     "  ·culos - Inserta la cara de alguien en un culo")

import subprocess
import re
import os
def get_destination_path(path, file_url):
    down_file = os.path.join(path, os.path.basename(file_url))
    new_file = os.path.join(path, os.path.splitext(
                os.path.basename(file_url))[0]) + '.pdf'
    return down_file, new_file
def document_saver(bot, update):
    if update.message.document and check_document(update.message.document.file_name):
        last_document = update.message.document
        try:
            doc_file = bot.getFile(last_document.file_id)
            my_path = os.path.abspath(os.path.dirname(__file__))
            down, new = get_destination_path(my_path, update.message.document.file_name)
            doc = doc_file.download(down)
            convert_to(my_path, update.message.document.file_name)
            bot.sendMessage(chat_id=update.message.chat_id,
                            text='Converting "%s"!' % update.message.document.file_name)
            bot.send_document(chat_id=update.message.chat_id,
                              document=open(new, 'rb'))
            if os.path.exists(doc):
                os.remove(doc)
            if os.path.exists(new):
                os.remove(new)
        except Exception as e:
            logger.error('Error:%s' % e)
            bot.sendMessage(chat_id=update.message.chat_id,
                            text="Error! :(")
    else:
        bot.sendMessage(chat_id=update.message.chat_id,
                        text="I'm only able to convert DOCX and DOC files!")
def check_document(file_name):
    return file_name.endswith('.docx') or file_name.endswith('.doc')
def convert_to(folder, source):
    args = ['libreoffice', '--headless', '--convert-to', 'pdf', '--outdir', folder, source]
    process = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=None)
    file = re.search('-> (.*?) using filter', process.stdout.decode())
    return file.group(1)
if __name__ == "__main__":
    load_dotenv()
    my_bot = Bot(token=TOKEN)
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
            ESTADO_UNICO: [MessageHandler(Filters.photo & ~Filters.command, culos2)]

        },
        fallbacks=[CommandHandler('culos', culos)],
    )
    conv_handler_pietrobot = ConversationHandler(
        entry_points=[CommandHandler('pietrobot', pietrobot)],
        states={
            ESTADO_UNICO: [MessageHandler(Filters.text & ~Filters.command, end_pietrobot)]

        },
        fallbacks=[CommandHandler('pietrobot', pietrobot)],

    )

    dp.add_handler(MessageHandler(Filters.document, document_saver))
    dp.add_handler(listas.conv_handler_listas)
    dp.add_handler(tesoreria.conv_handler_tesoreria)
    dp.add_handler(conv_handler_loquendo)
    dp.add_handler(conv_handler_pietrobot)
    dp.add_handler(birthday.conv_handler_birthday)
    dp.add_handler(conv_handler_culos)
    dp.add_handler(tareas.conv_handler_tareas)
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('cumples', birthday.get_birthday))
    dp.add_handler(CommandHandler('felicitar', birthday.birthday2))
    dp.add_handler(PollAnswerHandler(poll.receive_poll_answer))
    dp.add_handler(MessageHandler(Filters.poll, poll.receive_poll))
    dp.add_handler(CommandHandler('demo', poll.democracia))
    dp.add_handler(CommandHandler('bot', poll.bot_activado))
    dp.add_handler(drive.conv_handler_drive)

    dp.add_handler(MessageHandler(Filters.all, echo))

    job.run_daily(birthday.birthday, time(7, 00, 00, tzinfo=pytz.timezone('Europe/Madrid')))
    # job.run_daily(muditos, time(17, 54, 00, 000000))
    job.run_daily(tareas.recoradar_tareas, time(9, 00, 00, tzinfo=pytz.timezone('Europe/Madrid')), days=(1,))
    run(updater)
    logger.info(f"Iniciando el bot")
