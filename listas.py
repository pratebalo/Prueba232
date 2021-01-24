from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, Bot
from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    CallbackContext,
    MessageHandler,
    Filters
)
import pandas as pd
from datetime import datetime
import logging
import database as db

ELEGIR_LISTA, CREAR_LISTA1, CREAR_LISTA2, EDITAR_LISTA1, EDITAR_LISTA2, EDITAR_LISTA_A, EDITAR_LISTA_E, \
EDITAR_LISTA_O, ELIMINAR_LISTA1, VER_LISTA1 = range(10)
logger = logging.getLogger()


def listas(update: Update, context: CallbackContext):
    all_listas = db.select("listas")
    context.user_data["all_listas"] = all_listas
    chat_id = update.message.chat_id
    user = update.effective_user

    logger.info(f"{user.first_name} entró en el comando listas")
    keyboard = [
        [
            InlineKeyboardButton("Ver", callback_data="VER"),
            InlineKeyboardButton("Crear", callback_data="CREAR"),
            InlineKeyboardButton("Editar", callback_data="EDITAR"),
            InlineKeyboardButton("Eliminar", callback_data="ELIMINAR")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.sendMessage(chat_id, f"{user.first_name} ¿Qué quieres hacer?", reply_markup=reply_markup)
    context.bot.deleteMessage(chat_id, update.message.message_id)
    return ELEGIR_LISTA


def ver_lista(update: Update, context: CallbackContext):
    all_listas = context.user_data["all_listas"]

    logger.info(f"{update.effective_user.first_name} seleccionó ver listas")

    keyboard = []
    for i, lista in all_listas.iterrows():
        keyboard.append([InlineKeyboardButton(lista.nombre, callback_data=str(lista.id))])
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.callback_query.edit_message_text(
        text=f"{update.effective_user.first_name}: ¿Qué lista quieres ver?", reply_markup=reply_markup
    )
    return VER_LISTA1


def end_ver_lista(update: Update, context: CallbackContext):
    all_listas = context.user_data["all_listas"]
    lista = all_listas[all_listas.id == int(update.callback_query.data)].iloc[0]

    logger.info(f"{update.effective_user.first_name} seleccionó ver la lista {lista.nombre}")

    text = f"""{update.effective_user.first_name}""" \
           f""" ha solicitado ver la lista <b>{lista.nombre}</b>:\n"""

    for n, elemento in enumerate(lista.elementos):
        text += f"{n + 1}. {elemento}\n"

    update.callback_query.edit_message_text(parse_mode="HTML", text=text)

    return ConversationHandler.END


def crear_lista(update: Update, context: CallbackContext):
    query = update.callback_query

    logger.info(f"{update.effective_user.first_name} seleccionó crea lista")

    context.bot.deleteMessage(query.message.chat_id, query.message.message_id)
    context.user_data["oldMessage"] = context.bot.sendMessage(query.message.chat_id, parse_mode="Markdown",
                                                              text=f"{update.effective_user}: Escribe el nombre de la lista")

    return CREAR_LISTA1


def crear_lista2(update: Update, context: CallbackContext):
    message = update.message
    context.user_data["nombre_lista"] = message.text

    logger.info(f"{update.effective_user.first_name} eligio el nombre {message.text}")

    context.bot.deleteMessage(message.chat_id, message.message_id)
    context.user_data["oldMessage"] = context.bot.sendMessage(message.chat_id, parse_mode="Markdown",
                                                              text=f"{update.effective_user}: Escribe la lista en el siguiento formato:\n**Elemento1**\n**Elemento2** ")
    return CREAR_LISTA2


def end_crear_lista(update: Update, context: CallbackContext):

    logger.info(f"""{update.effective_user.first_name} ha escrito {update.message.text}""")

    context.bot.deleteMessage(context.user_data["oldMessage"].chat_id, context.user_data["oldMessage"].message_id)
    context.bot.deleteMessage(update.message.chat_id, update.message.message_id)
    text = f"""{update.effective_user.first_name} ha creado la lista <b>{context.user_data["nombre_lista"]}</b>:\n"""

    elementos = []
    for id, line in enumerate(update.message.text.splitlines()):
        text += f"{id + 1}. <b>{line}</b>\n"
        elementos.append(line)

    context.bot.sendMessage(update.message.chat_id, parse_mode="HTML", text=text)

    tipo_elementos = [0] * len(elementos)
    new_lista = pd.Series(
        {"nombre": context.user_data["nombre_lista"], "lista": elementos, "tipo_elementos": tipo_elementos,
         "creador": update.effective_user["id"],
         "fecha": datetime.today().strftime('%d/%m/%Y %H:%M'), "id": 0})
    db.insert_lista(new_lista)
    logger.info(f"""{update.effective_user.first_name} ha creado la lista {context.user_data["nombre_lista"]}""")

    return ConversationHandler.END


def editar_lista(update: Update, context: CallbackContext):
    query = update.callback_query
    all_listas = context.user_data["all_listas"]

    logger.info(f"""{update.effective_user.first_name} ha elegido editar lista""")

    keyboard = []
    for i, lista in all_listas.iterrows():
        keyboard.append([InlineKeyboardButton(lista.nombre, callback_data=str(lista.id))])
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(
        text=f"{update.effective_user.first_name}: ¿Qué lista quieres editar?", reply_markup=reply_markup
    )
    return EDITAR_LISTA1


def editar_lista2(update: Update, context: CallbackContext):
    query = update.callback_query
    all_listas = context.user_data["all_listas"]
    lista = all_listas[all_listas.id == int(query.data)].iloc[0]
    context.user_data["lista"] = lista

    logger.info(f"""{update.effective_user.first_name} ha elegido editar la lista {lista.nombre}""")

    keyboard = []
    for i, elem in enumerate(lista.elementos):
        keyboard.append([InlineKeyboardButton(elem, callback_data=str(i))])
    keyboard.append([InlineKeyboardButton("Añadir nuevo elemento", callback_data=str("AÑADIR"))])
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text=f"{update.effective_user.first_name}: Elige un elemento", reply_markup=reply_markup)

    return EDITAR_LISTA2


def editar_lista_o(update: Update, context: CallbackContext):
    # Añadir elementos
    keyboard = [[InlineKeyboardButton("Marcar", callback_data="MARK")],
                [InlineKeyboardButton("Editar", callback_data="EDIT")],
                [InlineKeyboardButton("Borrar", callback_data="DELETE")]
                ]
    context.user_data["element_pos"] = int(update.callback_query.data)
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.edit_message_text(
        text=f"{update.effective_user.first_name}: ¿Qué quiere hacer con el elemento?", reply_markup=reply_markup
    )
    return EDITAR_LISTA_O


def editar_lista_anadir(update: Update, context: CallbackContext):
    # Añadir elementos
    message = update.callback_query.message
    context.bot.deleteMessage(message.chat_id, message.message_id)
    context.user_data["oldMessage"] = context.bot.sendMessage(message.chat_id, parse_mode="HTML",
                                                              text=f"{update.effective_user.first_name}: Escribe los elementos a añadir en el siguiento formato:\n<b>Elemento1</b>\n<b>Elemento2</b> ")
    return EDITAR_LISTA_A


def end_editar_lista_anadir(update: Update, context: CallbackContext):
    context.bot.deleteMessage(context.user_data["oldMessage"].chat_id, context.user_data["oldMessage"].message_id)
    context.bot.deleteMessage(update.message.chat_id, update.message.message_id)

    lista = context.user_data["lista"]
    text = f"""{update.effective_user.first_name} ha editado la lista <b>{lista.nombre}</b>:\n"""
    for line in update.message.text.splitlines():
        lista.elementos.append(line)
        lista.tipo_elementos.append(0)

    for n, elemento in enumerate(lista.elementos):
        if lista.tipo_elementos[n] == 0:
            text += f"{n + 1}. {elemento}\n"
        elif lista.tipo_elementos[n] == 1:
            text += f"{n + 1}. <s>{elemento}</s>\n"

    context.bot.sendMessage(update.message.chat_id, parse_mode="HTML", text=text)
    logger.info(f"""{update.effective_user.first_name} ha editado la lista {lista.nombre}""")
    db.update_lista(lista)

    return ConversationHandler.END


def end_editar_lista_eliminar(update: Update, context: CallbackContext):
    lista = context.user_data["lista"]
    lista.elementos.pop(context.user_data["element_pos"])
    lista.tipo_elementos.pop(context.user_data["element_pos"])
    context.bot.deleteMessage(update.callback_query.message.chat_id, update.callback_query.message.message_id)
    text = f"""{update.effective_user.first_name} ha editado la lista <b>{lista.nombre}</b>:\n"""

    for n, elemento in enumerate(lista.elementos):
        if lista.tipo_elementos[n] == 0:
            text += f"{n + 1}. {elemento}\n"
        elif lista.tipo_elementos[n] == 1:
            text += f"{n + 1}. <s>{elemento}</s>\n"

    context.bot.sendMessage(update.callback_query.message.chat_id, parse_mode="HTML", text=text)

    logger.info(f"""{update.effective_user.first_name} ha editado la lista {lista.nombre}""")
    db.update_lista(lista)
    return ConversationHandler.END


def end_editar_lista_marcar(update: Update, context: CallbackContext):
    lista = context.user_data["lista"]
    pos_elemento = context.user_data["element_pos"]
    lista.tipo_elementos[pos_elemento] = 1
    context.bot.deleteMessage(update.callback_query.message.chat_id, update.callback_query.message.message_id)
    text = f"""{update.callback_query.from_user.first_name} ha editado la lista <b>{lista.nombre}</b>:\n"""
    for n, elemento in enumerate(lista.elementos):
        if lista.tipo_elementos[n] == 0:
            text += f"{n + 1}. {elemento}\n"
        elif lista.tipo_elementos[n] == 1:
            text += f"{n + 1}. <s>{elemento}</s>\n"

    context.bot.sendMessage(update.callback_query.message.chat_id, parse_mode="HTML", text=text)
    db.update_lista(lista)

    return ConversationHandler.END


def editar_lista_editar(update: Update, context: CallbackContext):
    message = update.callback_query.message
    context.bot.deleteMessage(message.chat_id, message.message_id)
    context.bot.sendMessage(message.chat_id, parse_mode="HTML", text="Escribe el nuevo elemento")
    return EDITAR_LISTA_E


def end_editar_lista_editar(update: Update, context: CallbackContext):
    lista = context.user_data["lista"]
    lista.elementos[context.user_data["element_pos"]] = update.message.text
    context.bot.deleteMessage(update.message.chat_id, update.message.message_id)
    text = f"""{update.effective_user.first_name} ha editado la lista <b>{lista.nombre}</b>:\n"""
    for n, elemento in enumerate(lista.elementos):
        text += f"{n + 1}. {elemento}\n"

    context.bot.sendMessage(update.message.chat_id, parse_mode="HTML", text=text)
    db.update_lista(lista)
    return ConversationHandler.END


def eliminar_lista(update: Update, context: CallbackContext):
    query = update.callback_query
    keyboard = []
    all_listas = context.user_data["all_listas"]
    for _, lista in all_listas.iterrows():
        keyboard.append([InlineKeyboardButton(lista.nombre, callback_data=lista.id)])
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(
        text=f"{update.effective_user.first_name}: ¿Qué lista quieres eliminar?", reply_markup=reply_markup
    )
    return ELIMINAR_LISTA1


def end_eliminar_lista(update: Update, context: CallbackContext):
    lista = db.delete("listas", int(update.callback_query.data)).iloc[0]
    update.callback_query.edit_message_text(parse_mode="HTML",
                                            text=f"{update.effective_user.first_name} ha eliminado la lista \n<b>{lista.nombre}</b>")
    return ConversationHandler.END


conv_handler_listas = ConversationHandler(
    entry_points=[CommandHandler('listas', listas)],
    states={
        ELEGIR_LISTA: [
            CallbackQueryHandler(ver_lista, pattern='^VER$'),
            CallbackQueryHandler(crear_lista, pattern='^CREAR$'),
            CallbackQueryHandler(editar_lista, pattern='^EDITAR$'),
            CallbackQueryHandler(eliminar_lista, pattern='^ELIMINAR$')
        ],
        CREAR_LISTA1: [MessageHandler(Filters.text & ~Filters.command, crear_lista2)],
        CREAR_LISTA2: [MessageHandler(Filters.text & ~Filters.command, end_crear_lista)],
        EDITAR_LISTA1: [CallbackQueryHandler(editar_lista2)],
        EDITAR_LISTA2: [CallbackQueryHandler(editar_lista_anadir, pattern='^AÑADIR$'),
                        CallbackQueryHandler(editar_lista_o)],
        EDITAR_LISTA_A: [MessageHandler(Filters.text & ~Filters.command, end_editar_lista_anadir)],
        EDITAR_LISTA_E: [MessageHandler(Filters.text & ~Filters.command, end_editar_lista_editar)],
        EDITAR_LISTA_O: [
            CallbackQueryHandler(end_editar_lista_marcar, pattern='^MARK$'),
            CallbackQueryHandler(editar_lista_editar, pattern='^EDIT$'),
            CallbackQueryHandler(end_editar_lista_eliminar, pattern='^DELETE$')
        ],
        ELIMINAR_LISTA1: [CallbackQueryHandler(end_eliminar_lista)],
        VER_LISTA1: [CallbackQueryHandler(end_ver_lista)]

    },
    fallbacks=[CommandHandler('listas', listas)],
)
