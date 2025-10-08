# main.py (Corrected for python-telegram-bot v5.0.0)

import gettext
import redis
import telegram

from functools import wraps
from telegram.ext import Updater, CommandHandler, MessageHandler,\
                         RegexHandler, Filters

import config

# Connecting to Telegram API
updater = Updater(token=config.TOKEN)
dispatcher = updater.dispatcher

# Config the translations
lang_pt = gettext.translation("helpdeskbot", localedir="locale", languages=["pt_BR"])
def _(msg): return msg

# Connecting to Redis db
db = redis.StrictRedis(host=config.REDIS_HOST,
                       port=config.REDIS_PORT,
                       db=config.REDIS_DB,
                       decode_responses=True) # Easier to work with strings


def user_language(func):
    @wraps(func)
    def wrapped(bot, update, *args, **kwargs):
        lang = db.get(f"lang:{update.message.chat_id}") # Use a prefix for clarity

        global _

        if lang == "pt_BR":
            _ = lang_pt.gettext
        else:
            def _(msg): return msg

        result = func(bot, update, *args, **kwargs)
        return result
    return wrapped


@user_language
def start(bot, update):
    """
        Shows an welcome message and help info about the available commands.
    """
    me = bot.get_me()
    if config.START_MESSAGE:
        msg = config.START_MESSAGE
    else:
        msg = _("Hello!\n")
        msg += _("I'm {0} and I came here to help you.\n").format(me.first_name)
        msg += _("What would you like to do?\n\n")
        msg += _("/support - Opens a new support ticket\n")
        msg += _("/settings - Settings of your account\n\n")
    main_menu_keyboard = [[telegram.KeyboardButton('/support')],
                          [telegram.KeyboardButton('/settings')]]
    reply_kb_markup = telegram.ReplyKeyboardMarkup(main_menu_keyboard,
                                                   resize_keyboard=True,
                                                   one_time_keyboard=True)
    bot.send_message(chat_id=update.message.chat_id,
                     text=msg,
                     reply_markup=reply_kb_markup)


@user_language
def support(bot, update):
    """
        Sends the support message. Some kind of "How can I help you?".
    """
    bot.send_message(chat_id=update.message.chat_id,
                     text=_("Please, tell me what you need support with :)"))


@user_language
def support_message(bot, update):
    """
        Receives a message from the user or a reply from an agent.
    """
    # Check if the message is from the support group AND is a reply
    if update.message.chat_id == config.GROUP_CHAT_ID and update.message.reply_to_message:
        # It's a reply from an agent in the group.
        # Look up the original user's chat_id in Redis.
        user_chat_id = db.get(f"ticket:{update.message.reply_to_message.message_id}")
        
        if user_chat_id:
            # We found the user, send them the agent's reply.
            bot.send_message(chat_id=user_chat_id, text=update.message.text)
    
    # Check if the message is a private message to the bot
    elif update.message.chat.type == 'private':
        # It's a message from a user. Forward it to the support group.
        forwarded_message = bot.forward_message(
            chat_id=config.GROUP_CHAT_ID,
            from_chat_id=update.message.chat_id,
            message_id=update.message.message_id
        )
        
        # Store the mapping in Redis. Expire after 7 days (604800 seconds).
        db.set(
            f"ticket:{forwarded_message.message_id}",
            update.message.chat_id,
            ex=604800 
        )

        reply_text = config.REPLY_MESSAGE if config.REPLY_MESSAGE else _("Give me some time to think. Soon I will return to you with an answer.")
        bot.send_message(chat_id=update.message.chat_id, text=reply_text)
    
    # Other messages in the group that are not replies are ignored.


@user_language
def settings(bot, update):
    """
        Configure the messages language using a custom keyboard.
    """
    msg = _("Please, choose a language:\n")
    msg += "en_US - English (US)\n"
    msg += "pt_BR - Português (Brasil)\n"
    languages_keyboard = [
        [telegram.KeyboardButton('en_US - English (US)')],
        [telegram.KeyboardButton('pt_BR - Português (Brasil)')]
    ]
    reply_kb_markup = telegram.ReplyKeyboardMarkup(languages_keyboard,
                                                   resize_keyboard=True,
                                                   one_time_keyboard=True)
    bot.send_message(chat_id=update.message.chat_id,
                     text=msg,
                     reply_markup=reply_kb_markup)


@user_language
def kb_settings_select(bot, update, groups):
    """
        Updates the user's language based on it's choice.
    """
    chat_id = update.message.chat_id
    language = groups[0]
    languages = {"pt_BR": "Português (Brasil)", "en_US": "English (US)"}

    if language in languages.keys():
        db.set(f"lang:{chat_id}", language)
        bot.send_message(chat_id=chat_id,
                         text=_("Language updated to {0}")
                         .format(languages[language]))
    else:
        bot.send_message(chat_id=chat_id, text=_("Unknown language! :("))


@user_language
def unknown(bot, update):
    """
        Placeholder command when the user sends an unknown command.
    """
    msg = _("Sorry, I don't know what you're asking for.")
    bot.send_message(chat_id=update.message.chat_id, text=msg)


# --- Handler Definitions ---

start_handler = CommandHandler('start', start)
support_handler = CommandHandler('support', support)
settings_handler = CommandHandler('settings', settings)
help_handler = CommandHandler('help', start)

get_language_handler = RegexHandler('^([a-z]{2}_[A-Z]{2}) - .*',
                                    kb_settings_select,
                                    pass_groups=True)

# Handler for any command that wasn't recognized by the handlers above.
unknown_handler = MessageHandler([Filters.command], unknown)

# Handler for any text message. This logic relies on this handler being added LAST.
support_msg_handler = MessageHandler([Filters.text], support_message)


# --- Handler Registration Order ---
# The order is critical for the logic to work correctly.

dispatcher.add_handler(start_handler)
dispatcher.add_handler(support_handler)
dispatcher.add_handler(settings_handler)
dispatcher.add_handler(help_handler)

dispatcher.add_handler(get_language_handler)

# The handler for unknown commands must be after all valid command handlers.
dispatcher.add_handler(unknown_handler)

# The general message handler MUST be last, so it only catches messages
# that are not commands.
dispatcher.add_handler(support_msg_handler)