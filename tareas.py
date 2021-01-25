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
import random
from datetime import date
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP

# Stages
ELEGIR_TAREA, CREAR_TAREA1, CREAR_TAREA2, CREAR_TAREA3, CREAR_TAREA4, \
CREAR_TAREA5, EDITAR_TAREA1, ELIMINAR_TAREA1, VER_TAREA = range(9)
#pruebas
#ID_MANITOBA = -1001307358592
#llavens
ID_MANITOBA = -1001255856526
logger = logging.getLogger()


def tareas(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    user = update.message.from_user
    context.user_data["creador_tarea"] = user["id"]
    logger.info(f"{user.first_name} entro en el comando tareas")
    all_tareas = db.select("tareas")
    data = db.select("data")
    context.user_data["data"] = data
    context.user_data["all_tareas"] = all_tareas
    keyboard = [InlineKeyboardButton("Crear", callback_data=str("CREAR"))]
    if len(all_tareas) > 0:
        keyboard.append(InlineKeyboardButton("Ver", callback_data=str("VER")))
        keyboard.append(InlineKeyboardButton("Editar", callback_data=str("EDITAR")))
        keyboard.append(InlineKeyboardButton("Eliminar", callback_data=str("ELIMINAR")))
    reply_markup = InlineKeyboardMarkup([keyboard])
    # Send message with text and appended InlineKeyboard
    context.bot.sendMessage(chat_id, "¿Qué quieres hacer?", reply_markup=reply_markup)
    context.bot.deleteMessage(chat_id, update.message.message_id)
    # Tell ConversationHandler that we're in state `FIRST` now
    context.user_data["personas_asignadas"] = []
    return ELEGIR_TAREA


def ver_tarea(update: Update, context: CallbackContext):
    all_tareas = context.user_data["all_tareas"]
    logger.info(f"{update.effective_user.first_name} seleccionó ver tareas")

    keyboard = []
    for i, tarea in all_tareas.iterrows():
        keyboard.append([InlineKeyboardButton(tarea.descripcion, callback_data=str(tarea.id))])
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.callback_query.edit_message_text(
        text=f"{update.effective_user.first_name}: ¿Qué tarea quieres ver?", reply_markup=reply_markup
    )
    return VER_TAREA


def end_ver_tarea(update: Update, context: CallbackContext):
    all_tareas = context.user_data["all_tareas"]
    data = context.user_data["data"]
    tarea = all_tareas[all_tareas.id == int(update.callback_query.data)].iloc[0]
    print(tarea)
    logger.info(f"{update.effective_user.first_name} seleccionó ver la tarea '{tarea.descripcion}'")

    text = f"{update.effective_user.first_name} ha solicitado ver la tarea:\n"+tarea_to_text(tarea,data)

    update.callback_query.edit_message_text(parse_mode="HTML", text=text)

    return ConversationHandler.END


def crear_tarea(update: Update, context: CallbackContext):
    query = update.callback_query
    keyboard = []
    part_keyboard = []
    data = context.user_data["data"]
    for i, persona in data.sort_values(by="nombre", ignore_index=True).iterrows():
        part_keyboard.append(InlineKeyboardButton(persona.apodo, callback_data=str(persona.id)))
        if i % 3 == 2 or i == len(data):
            keyboard.append(part_keyboard)
            part_keyboard = []

    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.deleteMessage(query.message.chat_id, query.message.message_id)
    context.bot.sendMessage(query.message.chat_id, text="Creando tarea. ¿A quien quieres asignarla?",
                            reply_markup=reply_markup)
    logger.info(f"{update.effective_user.first_name} ha seleccionado crear tarea")
    return CREAR_TAREA1


def crear_tarea2(update: Update, context: CallbackContext):
    query = update.callback_query
    context.user_data["personas_asignadas"].append(int(query.data))
    keyboard = []
    part_keyboard = []
    data = context.user_data["data"]
    print(context.user_data["personas_asignadas"])
    for i, persona in data.sort_values(by="nombre", ignore_index=True).iterrows():
        if not persona.id in context.user_data["personas_asignadas"]:
            part_keyboard.append(InlineKeyboardButton(persona.apodo, callback_data=str(persona.id)))
        if i % 3 == 2 or i == len(data):
            keyboard.append(part_keyboard)
            part_keyboard = []
    keyboard.append([InlineKeyboardButton("NO", callback_data="NO")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    query.edit_message_text(text="Persona asignada. ¿Quieres asignarla a alguien más?", reply_markup=reply_markup)
    logger.info(f"{update.effective_user.first_name} ha asignado a {query.data} a la tarea")
    return CREAR_TAREA2


def elegir_fecha(update: Update, context: CallbackContext):
    query = update.callback_query
    calendar, step = DetailedTelegramCalendar().build()
    query.delete_message()
    context.bot.sendMessage(update.effective_chat.id, f"Select {LSTEP[step]}", reply_markup=calendar)
    return CREAR_TAREA3


def elegir_fecha2(update: Update, context: CallbackContext):
    result, key, step = DetailedTelegramCalendar().process(update.callback_query.data)
    if not result and key:
        context.bot.edit_message_text(f"Select {LSTEP[step]}",
                                      update.callback_query.message.chat_id,
                                      update.callback_query.message.message_id,
                                      reply_markup=key)
    elif result:
        context.bot.deleteMessage(
            update.callback_query.message.chat.id,
            update.callback_query.message.message_id)
        result = result.strftime("%d/%m/%Y")
        context.user_data["fecha"] = result

        logger.info(f"{update.effective_user.first_name} ha elegido la fecha {result}")

        context.user_data["oldMessage"] = context.bot.sendMessage(update.effective_chat.id,
                                                                  text="Introduce la descripcion")
        return CREAR_TAREA4


def end_creacion(update: Update, context: CallbackContext):
    data = context.user_data["data"]
    message = update.message
    logger.info(f"{update.effective_user.first_name} ha indicado  la descripcion {message.text}")
    tarea = pd.Series({"descripcion": message.text, "personas": context.user_data["personas_asignadas"],
                       "fecha": context.user_data["fecha"], "creador": context.user_data["creador_tarea"]})

    context.bot.deleteMessage(context.user_data["oldMessage"].chat_id, context.user_data["oldMessage"].message_id)
    context.bot.deleteMessage(message.chat_id, message.message_id)

    text = f"""{update.effective_user.first_name} ha creado la tarea:\n"""+tarea_to_text(tarea,data)


    db.insert_tarea(tarea)
    context.bot.sendMessage(message.chat_id, parse_mode="HTML", text=text)
    sticker = ["CAACAgIAAx0CTey1gAACAiJgDvqYZC9VcMAvbJu8c_LKDD4R-gACigAD9wLID_jyogIDMJ9NHgQ",
               "CAACAgIAAx0CTey1gAACAiNgDvqb4ZQnkhOJqxBxcfNeC6PKiAACDAEAAvcCyA8bE6ozG0L6sx4E",
               "CAACAgIAAx0CTey1gAACAiRgDvqdnzEjoQWAhx8ixlNBsr89HgAC8wADVp29Cmob68TH-pb-HgQ",
               "CAACAgIAAx0CTey1gAACAiVgDvqp-x4WxBTpA_8BLeNZHmgTLQACDgADwDZPEyNXFESHbtZlHgQ",
               "CAACAgIAAx0CTey1gAACAiZgDvq1usw0Bk8BhySorPlmW4MIUwACNAADWbv8JWBOiTxAs-8HHgQ",
               "CAACAgIAAx0CTey1gAACAidgDvq9Hg4rMGs1decm0hjCn21HOgACCAEAAvcCyA_dAQAB7MrQa-UeBA"]

    personas = data[data.id.isin(tarea.personas)]
    for _, persona in personas.iterrows():
        try:
            context.bot.sendMessage(persona.id, parse_mode="HTML",
                                    text="Se te ha asignado la siguiente tarea:\n" + text)
        except:
            context.bot.sendMessage(ID_MANITOBA, text=f"{persona.apodo} no me tiene activado")
            context.bot.sendSticker(ID_MANITOBA, sticker=sticker[random.randint(0, len(sticker) - 1)])
    logger.info(f"Se ha creado la tarea {tarea.descripcion}")

    return ConversationHandler.END


def editar_tarea(update: Update, context: CallbackContext):
    """Show new choice of buttons"""
    query = update.callback_query
    query.answer()
    keyboard = []
    all_tareas = context.user_data["all_tareas"]
    for _, tarea in all_tareas.iterrows():
        keyboard.append([InlineKeyboardButton(tarea.descripcion, callback_data=str(tarea.id))])
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
    all_tareas = context.user_data["all_tareas"]
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
    data=context.user_data["data"]
    if len(tarea) == 0:
        update.callback_query.edit_message_text(parse_mode="HTML",
                                                text=f"La tarea ya habia sido eliminada")
    else:
        update.callback_query.edit_message_text(parse_mode="HTML",
                                                text=f"Se ha eliminado la tarea \n<b>{tarea_to_text(tarea.iloc[0],data)}</b>")

    return ConversationHandler.END


def tarea_to_text(tarea, data):
    text = f"-<b>{tarea.descripcion}</b>:\n" \
           f"-<b>{tarea.fecha}</b>\n"
    personas = data[data.id.isin(tarea.personas)]
    for _, persona in personas.iterrows():
        text += f"  +{persona.apodo}\n"
    return text


conv_handler_tareas = ConversationHandler(
    entry_points=[CommandHandler('tareas', tareas)],
    states={
        ELEGIR_TAREA: [
            CallbackQueryHandler(crear_tarea, pattern='^' + str("CREAR") + '$'),
            CallbackQueryHandler(editar_tarea, pattern='^' + str("EDITAR") + '$'),
            CallbackQueryHandler(eliminar_tarea, pattern='^' + str("ELIMINAR") + '$'),
            CallbackQueryHandler(ver_tarea, pattern='^' + str("VER") + '$')
        ],
        CREAR_TAREA1: [CallbackQueryHandler(crear_tarea2)],
        CREAR_TAREA2: [
            CallbackQueryHandler(elegir_fecha, pattern='^NO$'),
            CallbackQueryHandler(crear_tarea2),
        ],
        CREAR_TAREA3: [CallbackQueryHandler(elegir_fecha2)],
        CREAR_TAREA4: [MessageHandler(Filters.text & ~Filters.command, end_creacion)],
        EDITAR_TAREA1: [CallbackQueryHandler(end_edicion)],
        ELIMINAR_TAREA1: [CallbackQueryHandler(end_eliminacion)],
        VER_TAREA: [CallbackQueryHandler(end_ver_tarea)]

    },
    fallbacks=[CommandHandler('tareas', tareas)],
)
