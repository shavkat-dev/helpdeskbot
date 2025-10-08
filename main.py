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
lang_ru = gettext.translation("helpdeskbot", localedir="locale", languages=["ru_RU"])
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
            # User has chosen Portuguese
            _ = lang_pt.gettext
        elif lang == "ru_RU" or lang is None:
            # User has chosen Russian OR is a new user (lang is None)
            # In both cases, we serve Russian.
            _ = lang_ru.gettext
        else:
            # This block now correctly handles the "en_US" case,
            # and acts as a safe fallback to English for any other value.
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
        msg = _("Hey there! I'm {0}, your friendly support bot.\n\nReady to help. What's up?\n").format(me.first_name)

    main_menu_keyboard = [
        [telegram.KeyboardButton(_("/support - Get help"))],
        [telegram.KeyboardButton(_("/settings - Change language"))]
    ]
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
                     text=_("Go for it! Just type your question or issue below."))


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

        # Confirmation message removed per updated product requirements.
    
    # Other messages in the group that are not replies are ignored.


@user_language
def settings(bot, update):
    """
        Configure the messages language using a custom keyboard.
    """
    msg = _("Pick your language:\n")
    languages_keyboard = [
        [telegram.KeyboardButton('🇺🇸 English')],
        [telegram.KeyboardButton('🇷🇺 Русский')],
        [telegram.KeyboardButton('🇧🇷 Português (Brasil)')]
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
    choice = groups[0]

    languages = {
        "English": ("en_US", "English"),
        "Русский": ("ru_RU", "Русском"),
        "Português (Brasil)": ("pt_BR", "Português (Brasil)")
    }

    if choice in languages:
        lang_code, lang_name = languages[choice]
        db.set(f"lang:{chat_id}", lang_code)
        bot.send_message(chat_id=chat_id,
                         text=_("All set! We'll chat in {0} from now on.")
                         .format(lang_name))
    else:
        bot.send_message(chat_id=chat_id, text=_("Hmm, I don't recognize that language. Please pick from the list."))


@user_language
def unknown(bot, update):
    """
        Placeholder command when the user sends an unknown command.
    """
    msg = _("Oops, not sure what that command does. Try /support or /settings.")
    bot.send_message(chat_id=update.message.chat_id, text=msg)


# --- Handler Definitions ---

start_handler = CommandHandler('start', start)
support_handler = CommandHandler('support', support)
settings_handler = CommandHandler('settings', settings)
help_handler = CommandHandler('help', start)

get_language_handler = RegexHandler('^(?:🇺🇸 |🇷🇺 |🇧🇷 )(English|Русский|Português \(Brasil\))',
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
