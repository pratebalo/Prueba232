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
from datetime import datetime, time, timedelta
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
import os
import listas
import tareas
import tesoreria

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger()

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

        updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN)
        updater.bot.set_webhook(f"https://{HEROKU_APP_NAME}.herokuapp.com/{TOKEN}")
else:
    sys.exit()


def birthday(context: CallbackContext):
    data = db.select("data")
    fecha = datetime.today().strftime('%d/%m')
    cumpleaneros = data[data.cumple == fecha]
    stickers=["CAACAgIAAxkBAAIEO2AvpKPDrRqnQQ4VkXJuI_FYpTKdAALRAAP3AsgPsNUWIvohscweBA"]
    for _, cumpleanero in cumpleaneros.iterrows():
        tts = gTTS("""Estas son las mañanitas

                        De Jorgito del Mas Ojeis
                        
                        Para ti querida amiga
                        
                        Que cumples ya 106
                        
                        Despierta floja, despierta
                        
                        Mira que ya amaneció
                        
                        Ya los telocolotes cantan
                        
                        El burro ya rebuznó
                        
                        El día que tú naciste nacieron los dinosaurios,
                        
                        Las vacas no dieron leche
                        
                        Y lloraron los cavernarios
                        Escuchen, listen Chicken
                        Se vienens, ya comienza, 
                        Abrid bien las orejas:
                        
                        Tú no eres tímida, tú no eres tibia
                        Me das envidia, ah. Contigo quiero estar
                        Eres mi amiga y mi maestra
                        Lidya, mujer anfibia
                        Contigo sé que no me voy a apalancar
                        Mi Cleopatra, llévame a Nueva York
                        Quiero pasear a tu lado, anónimo
                        Como si fuéramos los últimos romanticistas
                        Que bailan abrazados entre los turistas
                        
                        
                        Perdona lo mal cantado
                        
                        Y también lo mal habido
                        
                        Si no te trajimos nada
                        
                        Es que estamos bien jodidos
                        
                        Ahí viene el Chupa cabras
                        
                        Y el hombre lobo también
                        
                        Ya se despertó la momia
                        
                        Que te va a jalar los pies
                        
                        Sapo verde eres tú
                        
                        Sapo verde eres tú
                        
                        Sapo verde eres tú con ganas
                        
                        Sapo verde eres tú
                        
                        
                        Plas e plas i plas eoeoe plas plas plas 
                        Currucutumtum currutas 
                        Chova, chova, cada día me gustas más
                        Plas plas plasenensensen
                        Plas plas plis plas Plus ensnsensnesnsenene plas plas 
                        Aplauso aplauso aplauso
                        Trafullaaaaa porongondo gondronsons flurucato de menta pa ti
                    """, lang="es")
        tts.save(f"Felicitacion de su majestad para {cumpleanero.apodo}.mp3")

        context.bot.sendMessage(chat_id=ID_MANITOBA, parse_mode="HTML",
                                text=f"Felicidades <b>{cumpleanero.apodo}</b>!!!!!")
        context.bot.sendSticker(chat_id=ID_MANITOBA,
                                sticker=random.choice(stickers))
        context.bot.sendAudio(chat_id=ID_MANITOBA,
                              audio=open(f"Felicitacion de su majestad para {cumpleanero.apodo}.mp3", "rb"))
        if cumpleanero.genero == "M":
            context.bot.sendMessage(chat_id=ID_MANITOBA, parse_mode="HTML",
                                    text=f"Por seeeeerrrr tan bueeeennaa muchaaaaachaaaaa 🎉🎊🎈")
        else:
            context.bot.sendMessage(chat_id=ID_MANITOBA, parse_mode="HTML",
                                    text=f"Por seeeeerrrr tan bueeeenn muchaaaaachaooooo 🎉🎊🎈")


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
            if update.message:
                texto= update.message.text
            elif update.poll:
                texto= update.poll.question
            mensaje = context.bot.sendMessage(chat_id=ID_MANITOBA, parse_mode="HTML",
                                              text=f"Se ha iniciado una conversacion: <a href='https://t.me/c/1462256012/{update.message.message_id}?thread={update.message.message_id}'>{texto}</a>")
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
            db.update_data(fila)
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
                logger.info(
                    f"{update.effective_chat.type} -> {fila.apodo} ha enviado el documento {update.message.document.file_name} tipo "
                    f"{update.message.document.mime_type}. Con un total de {fila.total_mensajes} mensajes")
            elif update.message.new_chat_members:
                logger.info(
                    f"{update.effective_chat.type} -> {update.message.new_chat_members} ha entrado al grupo ")
            else:
                logger.info(f"{update.effective_chat.type} -> update.message desconocido:  {update.message}")
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
    dp.add_handler(listas.conv_handler_listas)
    dp.add_handler(tesoreria.conv_handler_tesoreria)
    dp.add_handler(conv_handler_loquendo)
    dp.add_handler(conv_handler_pietrobot)
    dp.add_handler(conv_handler_culos)
    dp.add_handler(tareas.conv_handler_tareas)
    dp.add_handler(CommandHandler('start', start))

    dp.add_handler(MessageHandler(Filters.all, echo))

    job.run_daily(birthday, time(6, 00, 00, 000000))
    # job.run_daily(muditos, time(17, 54, 00, 000000))
    job.run_daily(tareas.recoradar_tareas, time(9, 00, 00, 000000), days=(1,))
    run(updater)
