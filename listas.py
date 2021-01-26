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
EDITAR_LISTA_O = range(8)
ID_MANITOBA = -1001255856526
logger = logging.getLogger()


def listas(update: Update, context: CallbackContext):
    all_listas = db.select("listas")
    context.user_data["all_listas"] = all_listas
    chat_id = update.message.chat_id
    user = update.effective_user

    logger.info(f"{user.first_name} entró en el comando listas")

    keyboard = []
    text = f"{user.first_name} ¿Qué quieres hacer?\n"
    for i, lista in all_listas.iterrows():
        keyboardline = []
        text += f" {i + 1}. {lista.nombre}\n"
        keyboardline.append(InlineKeyboardButton(i + 1, callback_data="NADA"))
        keyboardline.append(InlineKeyboardButton("Ver", callback_data="VER" + str(lista.id)))
        keyboardline.append(InlineKeyboardButton("Editar", callback_data="EDITAR" + str(lista.id)))
        if lista.creador == user.id:
            keyboardline.append(InlineKeyboardButton("Eliminar", callback_data="ELIMINAR" + str(lista.id)))
        keyboard.append(keyboardline)
    keyboard.append([InlineKeyboardButton("Crear nueva lista", callback_data=str("CREAR"))])
    keyboard.append([InlineKeyboardButton("Terminar", callback_data=str("TERMINAR"))])
    reply_markup = InlineKeyboardMarkup(keyboard)

    context.bot.sendMessage(chat_id, text, reply_markup=reply_markup)
    context.bot.deleteMessage(chat_id, update.message.message_id)
    return ELEGIR_LISTA


def ver_lista(update: Update, context: CallbackContext):
    all_listas = context.user_data["all_listas"]
    id_lista = int(update.callback_query.data.replace("VER", ""))

    lista = all_listas[all_listas.id == id_lista].iloc[0]

    logger.info(f"{update.effective_user.first_name} seleccionó ver la lista '{lista.nombre}'")
    text = f"{update.effective_user.first_name} ha solicitado ver la lista:\n{lista_to_text(lista)}"

    update.callback_query.edit_message_text(parse_mode="HTML", text=text)

    return ConversationHandler.END


def crear_lista(update: Update, context: CallbackContext):
    query = update.callback_query

    logger.info(f"{update.effective_user.first_name} seleccionó crea lista")

    context.bot.deleteMessage(query.message.chat_id, query.message.message_id)
    context.user_data["oldMessage"] = context.bot.sendMessage(query.message.chat_id, parse_mode="Markdown",
                                                              text=f"{update.effective_user.first_name}: Escribe el nombre de la lista")

    return CREAR_LISTA1


def crear_lista2(update: Update, context: CallbackContext):
    message = update.message
    context.user_data["nombre_lista"] = message.text

    logger.info(f"{update.effective_user.first_name} eligio el nombre {message.text}")

    context.bot.deleteMessage(message.chat_id, message.message_id)
    context.bot.deleteMessage(context.user_data["oldMessage"].chat_id, context.user_data["oldMessage"].message_id)
    context.user_data["oldMessage"] = context.bot.sendMessage(message.chat_id, parse_mode="Markdown",
                                                              text=f"{update.effective_user.first_name}: Escribe la lista en el siguiento formato:\n**Elemento1**\n**Elemento2** ")
    return CREAR_LISTA2


def end_crear_lista(update: Update, context: CallbackContext):
    logger.info(f"""{update.effective_user.first_name} ha escrito {update.message.text}""")

    context.bot.deleteMessage(context.user_data["oldMessage"].chat_id, context.user_data["oldMessage"].message_id)
    context.bot.deleteMessage(update.message.chat_id, update.message.message_id)
    text = f"""{update.effective_user.first_name} ha creado la lista:\n<b>{context.user_data["nombre_lista"]}</b>:\n"""

    elementos = []
    for id, line in enumerate(update.message.text.splitlines()):
        text += f"  {id + 1}. <b>{line}</b>\n"
        elementos.append(line)

    context.bot.sendMessage(update.message.chat_id, parse_mode="HTML", text=text)

    tipo_elementos = [0] * len(elementos)
    new_lista = pd.Series(
        {"nombre": context.user_data["nombre_lista"], "elementos": elementos, "tipo_elementos": tipo_elementos,
         "creador": update.effective_user["id"],
         "fecha": datetime.today().strftime('%d/%m/%Y %H:%M'), "id": 0})
    db.insert_lista(new_lista)
    logger.info(f"""{update.effective_user.first_name} ha creado la lista {context.user_data["nombre_lista"]}""")

    return ConversationHandler.END


def editar_lista(update: Update, context: CallbackContext):
    query = update.callback_query
    all_listas = context.user_data["all_listas"]
    id_lista = int(update.callback_query.data.replace("EDITAR", ""))
    lista = all_listas[all_listas.id == id_lista].iloc[0]
    context.user_data["lista"] = lista

    logger.info(f"""{update.effective_user.first_name} ha elegido editar la lista '{lista.nombre}'""")

    keyboard = []
    for i, (elem, tipo) in enumerate(zip(lista.elementos, lista.tipo_elementos)):
        marcar = "✅" if tipo == 0 else "❌"
        keyboard.append([InlineKeyboardButton(elem, callback_data="NADA"),
                         InlineKeyboardButton("📝", callback_data="EDITAR" + str(i)),
                         InlineKeyboardButton(marcar, callback_data="MARCAR" + str(i)),
                         InlineKeyboardButton("🗑", callback_data="ELIMINAR" + str(i))])
    keyboard.append([InlineKeyboardButton("Añadir nuevos elementos", callback_data=str("AÑADIR"))])
    keyboard.append([InlineKeyboardButton("Termianr", callback_data=str("TERMINAR"))])
    reply_markup = InlineKeyboardMarkup(keyboard)
    print(query)
    query.delete_message()
    texto = f"{update.effective_user.first_name}: ¿Que quieres hacer?:\n{lista_to_text(lista)}"
    context.bot.sendMessage(update.effective_chat.id, parse_mode="HTML", text=texto,
                            reply_markup=reply_markup)

    return EDITAR_LISTA2


def editar_lista_o(update: Update, context: CallbackContext):
    query = update.callback_query
    all_listas = context.user_data["all_listas"]
    print(query.data)
    lista = context.user_data["lista"]

    logger.info(f"""{update.effective_user.first_name} ha elegido editar la lista '{lista.nombre}'""")

    keyboard = []
    for i, (elem, tipo) in enumerate(zip(lista.elementos, lista.tipo_elementos)):
        marcar = "Marcar" if tipo == 0 else "Desmarcar"
        keyboard.append([InlineKeyboardButton(str(i + 1), callback_data="NADA"),
                         InlineKeyboardButton("Editar", callback_data="EDITAR" + str(i)),
                         InlineKeyboardButton(marcar, callback_data="MARCAR" + str(i)),
                         InlineKeyboardButton("Eliminar", callback_data="ELIMINAR" + str(i))])
    keyboard.append([InlineKeyboardButton("Añadir nuevo elemento", callback_data=str("AÑADIR"))])
    keyboard.append([InlineKeyboardButton("Terminar", callback_data=str("TERMINAR"))])
    reply_markup = InlineKeyboardMarkup(keyboard)
    print(query)
    query.delete_message()

    texto = f"{update.effective_user.first_name}: ¿Que quieres hacer?:\n{lista_to_text(lista)}"
    context.bot.sendMessage(update.effective_chat.id, parse_mode="HTML", text=texto,
                            reply_markup=reply_markup)

    return EDITAR_LISTA2


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
    for line in update.message.text.splitlines():
        lista.elementos.append(line)
        lista.tipo_elementos.append(0)

    texto = f"{update.effective_user.first_name} ha editado la lista:\n{lista_to_text(lista)}"

    context.bot.sendMessage(update.message.chat_id, parse_mode="HTML", text=texto)
    logger.info(f"""{update.effective_user.first_name} ha editado la lista '{lista.nombre}'""")
    db.update_lista(lista)

    return ConversationHandler.END


def end_editar_lista_eliminar(update: Update, context: CallbackContext):
    lista = context.user_data["lista"]
    pos_elemento = int(update.callback_query.data.replace("ELIMINAR", ""))
    lista.elementos.pop(pos_elemento)
    lista.tipo_elementos.pop(pos_elemento)
    context.bot.deleteMessage(update.callback_query.message.chat_id, update.callback_query.message.message_id)
    texto = f"{update.effective_user.first_name} ha editado la lista:\n{lista_to_text(lista)}"

    context.bot.sendMessage(update.callback_query.message.chat_id, parse_mode="HTML", text=texto)

    logger.info(f"""{update.effective_user.first_name} ha editado la lista '{lista.nombre}'""")
    db.update_lista(lista)
    return ConversationHandler.END


def end_editar_lista_marcar(update: Update, context: CallbackContext):
    lista = context.user_data["lista"]
    pos_elemento = int(update.callback_query.data.replace("MARCAR", ""))
    lista.tipo_elementos[pos_elemento] = 1 - lista.tipo_elementos[pos_elemento]
    context.bot.deleteMessage(update.callback_query.message.chat_id, update.callback_query.message.message_id)
    texto = f"{update.effective_user.first_name} ha editado la lista:\n{lista_to_text(lista)}"

    context.bot.sendMessage(update.callback_query.message.chat_id, parse_mode="HTML", text=texto)
    db.update_lista(lista)

    return ConversationHandler.END


def editar_lista_editar(update: Update, context: CallbackContext):
    message = update.callback_query.message
    context.bot.deleteMessage(message.chat_id, message.message_id)
    context.user_data["pos_elemento"] = int(update.callback_query.data.replace("EDITAR", ""))
    context.bot.sendMessage(message.chat_id, parse_mode="HTML", text="Escribe el nuevo elemento")
    return EDITAR_LISTA_E


def end_editar_lista_editar(update: Update, context: CallbackContext):
    lista = context.user_data["lista"]
    lista.elementos[context.user_data["pos_elemento"]] = update.message.text
    context.bot.deleteMessage(update.message.chat_id, update.message.message_id)
    texto = f"{update.effective_user.first_name} ha editado la lista:\n {lista_to_text(lista)}"

    context.bot.sendMessage(update.message.chat_id, parse_mode="HTML", text=texto)
    db.update_lista(lista)
    return ConversationHandler.END


def eliminar_lista(update: Update, context: CallbackContext):
    id_lista = int(update.callback_query.data.replace("ELIMINAR", ""))
    lista = db.delete("listas", id_lista).iloc[0]
    logger.info(f"""{update.effective_user.first_name} ha eliminado la lista '{lista.nombre}'""")
    texto = f"{update.effective_user.first_name} ha eliminado la lista:\n{lista_to_text(lista)}"
    update.callback_query.edit_message_text(parse_mode="HTML", text=texto)
    return ConversationHandler.END


def terminar(update: Update, context: CallbackContext):
    update.callback_query.delete_message()
    return ConversationHandler.END

def lista_to_text(lista):
    text = f"<b>{lista.nombre}</b>:\n"
    for n, elemento in enumerate(lista.elementos):
        if lista.tipo_elementos[n] == 0:
            text += f"  {n + 1}. {elemento}\n"
        else:
            text += f"  {n + 1}. <s>{elemento}</s>\n"
    return text

conv_handler_listas = ConversationHandler(
    entry_points=[CommandHandler('listas', listas)],
    states={
        ELEGIR_LISTA: [
            CallbackQueryHandler(ver_lista, pattern='^VER'),
            CallbackQueryHandler(crear_lista, pattern='^CREAR'),
            CallbackQueryHandler(editar_lista, pattern='^EDITAR'),
            CallbackQueryHandler(eliminar_lista, pattern='^ELIMINAR'),
            CallbackQueryHandler(terminar, pattern='^TERMINAR$')
        ],
        CREAR_LISTA1: [MessageHandler(Filters.text & ~Filters.command, crear_lista2)],
        CREAR_LISTA2: [MessageHandler(Filters.text & ~Filters.command, end_crear_lista)],
        EDITAR_LISTA2: [CallbackQueryHandler(editar_lista_anadir, pattern='^AÑADIR$'),
                        CallbackQueryHandler(editar_lista_o, pattern='^NADA$'),
                        CallbackQueryHandler(end_editar_lista_marcar, pattern='^MARCAR'),
                        CallbackQueryHandler(editar_lista_editar, pattern='^EDITAR'),
                        CallbackQueryHandler(end_editar_lista_eliminar, pattern='^ELIMINAR'),
                        CallbackQueryHandler(terminar, pattern='^TERMINAR$')],
        EDITAR_LISTA_A: [MessageHandler(Filters.text & ~Filters.command, end_editar_lista_anadir)],
        EDITAR_LISTA_E: [MessageHandler(Filters.text & ~Filters.command, end_editar_lista_editar)],
        EDITAR_LISTA_O: [],

    },
    fallbacks=[CommandHandler('listas', listas)],
)
