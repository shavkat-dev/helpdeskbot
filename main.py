# main.py (Modern, Async Version for python-telegram-bot v20+)

import gettext
import redis.asyncio as redis # Use the async version of the redis library
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

import config

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Translation Setup ---
# Pre-load translations
translations = {
    "pt_BR": gettext.translation("helpdeskbot", localedir="locale", languages=["pt_BR"]),
    "ru_RU": gettext.translation("helpdeskbot", localedir="locale", languages=["ru_RU"]),
}

async def get_translator(chat_id: int, db: redis.Redis):
    """Gets the correct translation function for a user. """
    lang = await db.get(f"lang:{chat_id}")
    if lang in translations:
        return translations[lang].gettext
    elif lang is None: # Default to Russian for new users
        return translations["ru_RU"].gettext
    else: # Fallback to English (source text)
        return lambda msg: msg

# --- Bot Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Greets the user and provides instructions."""
    _ = await get_translator(update.message.chat_id, context.bot_data["db"])
    me = await context.bot.get_me()
    msg = _("Hey there! I'm {0}, the official support for the @tgresearcherbot.\n\n"
            "To get help, just send your question, feedback, or issue directly into this chat. "
            "You can include photos and files. Our team will see it and get back to you as soon as possible.\n\n"
            "You can use /settings to change your language.").format(me.first_name)
    await update.message.reply_text(msg)

async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows the language selection menu."""
    _ = await get_translator(update.message.chat_id, context.bot_data["db"])
    msg = _("Pick your language:\n")
    languages_keyboard = [
        [KeyboardButton('🇺🇸 English')],
        [KeyboardButton('🇷🇺 Русский')],
        [KeyboardButton('🇧🇷 Português (Brasil)')]
    ]
    reply_markup = ReplyKeyboardMarkup(languages_keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(msg, reply_markup=reply_markup)

async def kb_settings_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Updates the user's language based on their choice."""
    db = context.bot_data["db"]
    _ = await get_translator(update.message.chat_id, db)
    choice = context.matches[0].group(1) # Get the captured group from regex

    languages = {
        "English": ("en_US", "English"),
        "Русский": ("ru_RU", "Русском"),
        "Português (Brasil)": ("pt_BR", "Português (Brasil)")
    }

    if choice in languages:
        lang_code, lang_name = languages[choice]
        await db.set(f"lang:{update.message.chat_id}", lang_code)
        await update.message.reply_text(_("All set! We'll chat in {0} from now on.").format(lang_name))
    else:
        await update.message.reply_text(_("Hmm, I don't recognize that language. Please pick from the list."))

async def support_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles messages from users (to be forwarded) or agents (to be replied)."""
    db = context.bot_data["db"]
    
    # Message is from an agent in the support group (and is a reply)
    if update.message.chat_id == config.GROUP_CHAT_ID and update.message.reply_to_message:
        user_chat_id = await db.get(f"ticket:{update.message.reply_to_message.message_id}")
        if user_chat_id:
            await context.bot.send_message(chat_id=int(user_chat_id), text=update.message.text)
    
    # Message is a private message from a user
    elif update.message.chat.type == 'private':
        forwarded_message = await context.bot.forward_message(
            chat_id=config.GROUP_CHAT_ID,
            from_chat_id=update.message.chat_id,
            message_id=update.message.message_id
        )
        # Store mapping with 7-day expiry
        await db.set(f"ticket:{forwarded_message.message_id}", update.message.chat_id, ex=604800)

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles unknown commands."""
    _ = await get_translator(update.message.chat_id, context.bot_data["db"])
    msg = _("Oops, not sure what that command does. You can use /settings or just send a message for support.")
    await update.message.reply_text(msg)


def main():
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(config.TOKEN).build()

    # --- Setup persistent context ---
    # Connect to Redis. We'll pass the connection pool to all handlers.
    db_pool = redis.ConnectionPool(host=config.REDIS_HOST, port=config.REDIS_PORT, db=config.REDIS_DB, decode_responses=True)
    db_connection = redis.Redis(connection_pool=db_pool)
    application.bot_data["db"] = db_connection

    # --- Register Handlers ---
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", start))
    application.add_handler(CommandHandler("settings", settings))
    
    application.add_handler(MessageHandler(filters.Regex(r'^(?:🇺🇸 |🇷🇺 |🇧🇷 )(English|Русский|Português \(Brasil\))'), kb_settings_select))
    
    # Handler for all text messages (for support tickets and replies)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, support_message))

    # Handler for all unknown commands must be last
    application.add_handler(MessageHandler(filters.COMMAND, unknown))

    # Run the bot until the user presses Ctrl-C
    logger.info("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()