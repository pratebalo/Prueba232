from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    CallbackContext,
    MessageHandler,
    Filters
)
import pandas as pd
import logging
import database as db

# Stages
ELEGIR_TAREA, CREAR_TAREA1, CREAR_TAREA2, CREAR_TAREA3, CREAR_TAREA4, \
CREAR_TAREA5, EDITAR_TAREA1, ELIMINAR_TAREA1 = range(8)

logger = logging.getLogger()


def tareas(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    user = update.message.from_user
    context.user_data["creador_tarea"] = user["id"]
    logger.info(f"{user.first_name} entro en el comando tareas")
    all_tareas = db.select("tareas")
    keyboard = [InlineKeyboardButton("Crear", callback_data=str("CREAR"))]
    if len(all_tareas) > 0:
        keyboard.append(InlineKeyboardButton("Editar", callback_data=str("EDITAR")))
        keyboard.append(InlineKeyboardButton("Eliminar", callback_data=str("ELIMINAR")))
    reply_markup = InlineKeyboardMarkup([keyboard])
    # Send message with text and appended InlineKeyboard
    context.bot.sendMessage(chat_id, "¿Qué quieres hacer?", reply_markup=reply_markup)
    context.bot.deleteMessage(chat_id, update.message.message_id)
    # Tell ConversationHandler that we're in state `FIRST` now
    context.user_data["personas_asignadas"] = []
    return ELEGIR_TAREA


def crear_tarea(update: Update, context: CallbackContext):
    query = update.callback_query
    keyboard = []
    part_keyboard = []
    data = db.select("data")
    context.user_data["data"] = data
    print(data.sort_values(by="nombre", ignore_index=True))
    for i, persona in data.sort_values(by="nombre", ignore_index=True).iterrows():
        part_keyboard.append(InlineKeyboardButton(persona["nombre"], callback_data=str(persona.user_id)))
        if i % 3 == 2 or i==len(data):
            keyboard.append(part_keyboard)
            part_keyboard = []

    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.deleteMessage(query.message.chat_id, query.message.message_id)
    context.bot.sendMessage(query.message.chat_id, text="Creando tarea. ¿A quien quieres asignarla?",
                            reply_markup=reply_markup)
    logger.info(f"{update.callback_query.from_user.first_name} ha seleccionado crear tarea")
    return CREAR_TAREA1


def crear_tarea2(update: Update, context: CallbackContext):
    """Show new choice of buttons"""
    query = update.callback_query
    logger.info(f"{update.callback_query.from_user.first_name} ha añadido a {query.data} a la tarea")
    context.user_data["personas_asignadas"].append(query.data)
    keyboard = [
        [
            InlineKeyboardButton("SI", callback_data="SI"),
            InlineKeyboardButton("NO", callback_data="NO")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(
        text="¿Quieres añadir alguien más?", reply_markup=reply_markup
    )
    return CREAR_TAREA2


def elegir_fecha(update: Update, context: CallbackContext):
    query = update.callback_query
    query.edit_message_text(text="Introduce la fecha en formato 02/12/2020")
    context.user_data["oldMessage"] = query.message
    return CREAR_TAREA3


def indicar_descripcion(update: Update, context: CallbackContext):
    message = update.message
    context.user_data["fecha"] = message.text
    logger.info(f"{update.message.from_user.first_name} ha elegido la fecha {message.text}")
    context.bot.deleteMessage(context.user_data["oldMessage"].chat_id, context.user_data["oldMessage"].message_id)
    context.bot.deleteMessage(message.chat_id, message.message_id)
    context.user_data["oldMessage"] = context.bot.sendMessage(message.chat_id, text="Introduce la descripcion")
    return CREAR_TAREA4


def end_creacion(update: Update, context: CallbackContext):
    data = context.user_data["data"]
    message = update.message
    logger.info(f"{update.message.from_user.first_name} ha indicado  la descripcion {message.text}")
    tarea = pd.Series({"descripcion": message.text, "personas": context.user_data["personas_asignadas"],
                       "fecha": context.user_data["fecha"], "creador": context.user_data["creador_tarea"]})

    context.bot.deleteMessage(context.user_data["oldMessage"].chat_id, context.user_data["oldMessage"].message_id)
    context.bot.deleteMessage(message.chat_id, message.message_id)

    text = f"""{data[data.user_id == update.effective_user["id"]].nombre.values[0]} ha creado la tarea:\n"""

    text += f"<b>{tarea.descripcion}</b>\n"
    text += f"Responsables:\n"
    print(tarea)
    print(tarea.personas)
    for persona in tarea.personas:
        text += f"- <b>{data[data.user_id == int(persona)].nombre_completo.values[0]}</b>\n"
    text += f"Fecha: <b>{tarea.fecha}</b>"
    context.bot.sendMessage(message.chat_id, parse_mode="HTML", text=text)

    logger.info(f"Persona2 {message.text}")
    db.insert_tarea(tarea)
    logger.info(f"Se ha creado la tarea")

    return ConversationHandler.END


def editar_tarea(update: Update, context: CallbackContext):
    """Show new choice of buttons"""
    query = update.callback_query
    query.answer()
    keyboard = []
    all_tareas = db.select("tareas")
    for _, tarea in all_tareas.iterrows():
        keyboard.append([InlineKeyboardButton(tarea.descripcion, callback_data=str(tarea.descripcion))])
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(
        text="Que tarea quieres editar", reply_markup=reply_markup
    )
    return EDITAR_TAREA1


def end_edicion(update: Update, context: CallbackContext):
    update.callback_query.edit_message_text(parse_mode="HTML",
                                            text=f"Se ha editado la tarea")
    return ConversationHandler.END


def eliminar_tarea(update: Update, context: CallbackContext):
    query = update.callback_query
    keyboard = []
    all_tareas = db.select("tareas")
    for _, tarea in all_tareas.iterrows():
        keyboard.append([InlineKeyboardButton(tarea.descripcion, callback_data=tarea.id)])
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(
        text="¿Qué tarea quieres eliminar?", reply_markup=reply_markup
    )
    return ELIMINAR_TAREA1


def end_eliminacion(update: Update, context: CallbackContext):
    """Returns `ConversationHandler.END`, which tells the
    # ConversationHandler that the conversation is over"""

    id_tarea = int(update.callback_query.data)
    tarea = db.delete("tareas", id_tarea)
    if len(tarea) == 0:
        update.callback_query.edit_message_text(parse_mode="HTML",
                                                text=f"La tarea ya habia sido eliminada")
    else:
        update.callback_query.edit_message_text(parse_mode="HTML",
                                                text=f"Se ha eliminado la tarea \n<b>{tarea.iloc[0].descripcion}</b>")

    return ConversationHandler.END


conv_handler_tareas = ConversationHandler(
    entry_points=[CommandHandler('tareas', tareas)],
    states={
        ELEGIR_TAREA: [
            CallbackQueryHandler(crear_tarea, pattern='^' + str("CREAR") + '$'),
            CallbackQueryHandler(editar_tarea, pattern='^' + str("EDITAR") + '$'),
            CallbackQueryHandler(eliminar_tarea, pattern='^' + str("ELIMINAR") + '$')
        ],
        CREAR_TAREA1: [CallbackQueryHandler(crear_tarea2)],
        CREAR_TAREA2: [
            CallbackQueryHandler(crear_tarea, pattern='^SI$'),
            CallbackQueryHandler(elegir_fecha, pattern='^NO$'),
        ],
        CREAR_TAREA3: [MessageHandler(Filters.text & ~Filters.command, indicar_descripcion)],
        CREAR_TAREA4: [MessageHandler(Filters.text & ~Filters.command, end_creacion)],
        EDITAR_TAREA1: [CallbackQueryHandler(end_edicion)],
        ELIMINAR_TAREA1: [CallbackQueryHandler(end_eliminacion)]

    },
    fallbacks=[CommandHandler('tareas', tareas)],
)
