import logging

from telegram import Update

from telegram.ext import (
    CallbackContext,
)
from utils import database as db

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)


def receive_poll_answer(update: Update, context: CallbackContext) -> None:
    """Summarize a users poll vote"""
    polls = db.select("encuestas")
    poll_id = update.poll_answer.poll_id
    poll = polls[polls.id == poll_id].squeeze()
    votes = poll.votes
    respuesta = update.poll_answer
    if not respuesta.option_ids:
        logger.warning(f"{update.effective_user.first_name} quito su voto de la encuesta {poll.question}")
        votes.remove(int(update.poll_answer.user.id))
        db.update_poll(poll_id, votes)
    else:
        votos = [poll.options[i] for i in respuesta.option_ids]
        logger.warning(f"{update.effective_user.first_name} ha votado {votos} en la encuesta {poll.question}")
        votes.append(int(update.poll_answer.user.id))
        db.update_poll(poll_id, votes)


def receive_poll(update: Update, context: CallbackContext) -> None:
    """On receiving polls, reply to it by a closed poll copying the received poll"""
    actual_poll = update.effective_message.poll
    logger.warning(f"{update.effective_user.first_name} ha creado la encuesta {actual_poll.question}")
    if not actual_poll.is_anonymous and not update.message.forward_from:

        update.effective_message.delete()
        options = [o.text for o in actual_poll.options]
        if update.message.reply_to_message:
            if update.message.reply_to_message.forward_from_chat:
                new_poll = context.bot.send_poll(
                    update.effective_chat.id,
                    question=actual_poll.question,
                    options=options,
                    is_anonymous=False,
                    allows_multiple_answers=actual_poll.allows_multiple_answers,
                    reply_to_message_id=update.message.reply_to_message.message_id
                )

                url = f"https://t.me/c/{str(new_poll.chat.id)[4:]}/{new_poll.message_id}?thread={update.message.reply_to_message.message_id}"
            else:
                new_poll = context.bot.send_poll(
                    update.effective_chat.id,
                    question=actual_poll.question,
                    options=options,
                    is_anonymous=False,
                    allows_multiple_answers=actual_poll.allows_multiple_answers
                )
                url = f"https://t.me/c/{str(new_poll.chat.id)[4:]}/{new_poll.message_id}"
        else:
            new_poll = context.bot.send_poll(
                update.effective_chat.id,
                question=actual_poll.question,
                options=options,
                is_anonymous=False,
                allows_multiple_answers=actual_poll.allows_multiple_answers
            )
            url = f"https://t.me/c/{str(new_poll.chat.id)[4:]}/{new_poll.message_id}"

        db.insert_poll(new_poll.poll.id, new_poll.poll.question, options, new_poll.poll.is_anonymous, [], url)


def democracia(update: Update, context: CallbackContext) -> None:
    logger.warning(f"{update.effective_user.first_name} ha ejecutado el comando democracia")
    data = db.select("data")
    encuestas = db.select("encuestas")
    encuestas = encuestas[~encuestas.end]
    for _, persona in data.iterrows():
        questions = ""
        for _, encuesta in encuestas.iterrows():
            if persona.id not in encuesta.votes:
                questions += f"- <a href='{encuesta.url}'>{encuesta.question}</a>\n"

        if questions:
            text = f"{persona.apodo}, al vivir en una democracia tienes derecho a votar en las encuestas\n" + questions
            try:
                context.bot.sendMessage(chat_id=persona.id, parse_mode="HTML", text=text)
            except:
                print(f"{persona.apodo} con id {persona.id} NO tiene activado el bot")


def bot_activado(update: Update, context: CallbackContext) -> None:

    logger.warning(f"{update.effective_user.first_name} ha ejecutado el comando bot_activado")
    data = db.select("data")
    for _, persona in data.iterrows():
        try:
            mensaje = context.bot.sendMessage(chat_id=persona.id, parse_mode="HTML", text="prueba")
            context.bot.deleteMessage(mensaje.chat_id, mensaje.message_id)
            # print(f"{persona.apodo} con id {persona.id} tiene activado el bot")
        except:
            print(f"{persona.apodo} con id {persona.id} NO tiene activado el bot")
