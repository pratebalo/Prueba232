import logging

from telegram import Update

from telegram.ext import (
    Updater,
    CommandHandler,
    PollAnswerHandler,
    MessageHandler,
    Filters,
    CallbackContext,
)
import pandas as pd
import database as db

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)


def receive_poll_answer(update: Update, context: CallbackContext) -> None:
    """Summarize a users poll vote"""
    polls = db.select("encuestas")
    poll_id = update.poll_answer.poll_id
    votes = polls[polls.id == poll_id].votes.iloc[0]
    respuesta = update.poll_answer
    if not respuesta.option_ids:
        print("Voto retractado")
        votes.remove(int(update.poll_answer.user.id))
        db.update_poll(poll_id, votes)
    else:
        print(f"Ha votado  {respuesta.option_ids}")
        votes.append(int(update.poll_answer.user.id))
        db.update_poll(poll_id, votes)


def receive_poll(update: Update, context: CallbackContext) -> None:
    """On receiving polls, reply to it by a closed poll copying the received poll"""
    actual_poll = update.effective_message.poll
    if not actual_poll.is_anonymous and not update.message.forward_from:

        update.effective_message.delete()
        options = [o.text for o in actual_poll.options]
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

        db.insert_poll(new_poll.poll.id, new_poll.poll.question, options, new_poll.poll.is_anonymous, [], url)


def democracia(update: Update, context: CallbackContext) -> None:
    print(update)
    data = db.select("data")
    encuestas = db.select("encuestas")
    encuestas = encuestas[~encuestas.end]
    print(encuestas)
    for _, persona in data.iterrows():
        questions = ""
        for _, encuesta in encuestas.iterrows():
            if persona.id not in encuesta.votes:
                questions += f"- <a href='{encuesta.url}'>{encuesta.question}</a>\n"

        if questions and persona.id == 8469898:
            text = f"{persona.apodo}, al vivir en una democracia tienes derecho a votar en las encuestas\n" + questions
            context.bot.sendMessage(chat_id=update.effective_chat.id, parse_mode="HTML", text=text)


def bot_activado(update: Update, context: CallbackContext) -> None:
    data = db.select("data")
    for _, persona in data.iterrows():
        try:
            mensaje = context.bot.sendMessage(chat_id=persona.id, parse_mode="HTML", text="prueba")
            context.bot.deleteMessage(mensaje.chat_id, mensaje.message_id)
            print(f"{persona.apodo} con id {persona.id} tiene activado el bot")
        except:
            print(f"{persona.apodo} con id {persona.id} NO tiene activado el bot")


def main() -> None:
    # Create the Updater and pass it your bot's token.    load_dotenv()
    #     my_bot = Bot(token=TOKEN)
    updater = Updater("1577490660:AAF5u3tAjpSIe7HDR6Hbq6BUGhiGE2imZ_o")
    dispatcher = updater.dispatcher

    # Start the Bot
    updater.start_polling()

    # Run the bot until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT
    updater.idle()


if __name__ == '__main__':
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', None)

    main()
