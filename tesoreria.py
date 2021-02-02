from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    CallbackContext,
    MessageHandler,
    Filters
)
import logging
import database as db
import re

# Stages
OPCION, BOTE, BOTE2, FINAL_OPTION = range(4)
# pruebas
# ID_MANITOBA = -1001307358592
# llavens
ID_MANITOBA = -1001255856526
ID_TESORERIA = 8469898
logger = logging.getLogger()


def tesoreria(update: Update, context: CallbackContext):
    context.user_data["bote"] = db.select("botes")
    gastos = db.select("gastos")
    logger.warning(f"{update.effective_user.first_name} entro en el comando tesoreria")
    # data = db.select("data")
    update.message.delete()
    text = "<b>Tesoreria</b>\n¿Qué quieres hacer?\n"
    keyboard = [[InlineKeyboardButton("Meter dinero en el bote", callback_data="+")],
                [InlineKeyboardButton("Sacar dinero del bote", callback_data="-")],
                [InlineKeyboardButton("Comunicar un gasto", callback_data="GASTO")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    context.bot.sendMessage(update.effective_chat.id, text, parse_mode="HTML", reply_markup=reply_markup)
    return OPCION


def bote(update: Update, context: CallbackContext):
    context.user_data["tipo"] = update.callback_query.data
    # context.user_data["oldMessage"] = context.bot.sendMessage(update.effective_chat.id, "¿Cuánto dinero?")
    context.user_data["oldMessage"] = update.callback_query.edit_message_text("¿Cuánto dinero?")

    return BOTE


def bote2(update: Update, context: CallbackContext):
    context.user_data["cantidad"] = re.sub('[^\d.]', '', update.message.text.replace(",", "."))
    context.bot.deleteMessage(update.effective_chat.id, context.user_data["oldMessage"].message_id)
    context.bot.deleteMessage(update.effective_chat.id, update.message.message_id)
    context.user_data["oldMessage"] = context.bot.sendMessage(update.effective_chat.id, "¿Cúal es el motivo?")

    return BOTE2


def bote3(update: Update, context: CallbackContext):
    if context.user_data["tipo"] == "GASTO":
        cantidad = float(context.user_data["cantidad"])
        db.insert_gastos(update.effective_user.id,
                         update.message.text,
                         cantidad)
        mensaje_tesorera = f"{update.effective_user.first_name} ha gastado {cantidad}€ en {update.message.text}"
        mensaje_usuario = f"Has metido el gasto de {cantidad}€ con el concepto '{update.message.text}'"
    else:
        cantidad = float(context.user_data["tipo"] + context.user_data["cantidad"])
        bote_actual = context.user_data["bote"].iloc[-1].total + cantidad
        db.insert_bote(update.effective_user.id,
                       cantidad,
                       bote_actual,
                       update.message.text)
        if context.user_data["tipo"] == "+":
            mensaje_tesorera = f"{update.effective_user.first_name} ha metido {context.user_data['cantidad']}€ " \
                               f"en el bote con el concepto '{update.message.text}'.\nHay {bote_actual}€ en el bote"
        else:
            mensaje_tesorera = f"{update.effective_user.first_name} ha sacado {context.user_data['cantidad']}€ " \
                               f"del bote con el concepto '{update.message.text}'.\nHay {bote_actual}€ en el bote"
        mensaje_usuario = f"Bote actualizado.\nHay {bote_actual}€ en el bote"

    context.bot.deleteMessage(update.effective_chat.id, context.user_data["oldMessage"].message_id)
    context.bot.deleteMessage(update.effective_chat.id, update.message.message_id)
    context.bot.sendMessage(update.effective_chat.id, mensaje_usuario)
    context.bot.sendMessage(8469898, mensaje_tesorera)

    return ConversationHandler.END


conv_handler_tesoreria = ConversationHandler(
    entry_points=[CommandHandler('tesoreria', tesoreria)],
    states={
        OPCION: [CallbackQueryHandler(bote)],
        BOTE: [MessageHandler(Filters.text & ~Filters.command, bote2)],
        BOTE2: [MessageHandler(Filters.text & ~Filters.command, bote3)],
    },
    fallbacks=[CommandHandler('tesoreria', tesoreria)],
)
