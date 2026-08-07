import logging

from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

COMMANDS = ["/start", "/help", "/id"]


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("chat.id=%s", update.effective_chat.id)
    await update.message.reply_text(
        "👋 I'm the Nastolka bot. I'll post here when a new game session is logged.\n"
        "Use /help to see what I can do."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("chat.id=%s", update.effective_chat.id)
    await update.message.reply_text(
        "Available commands:\n" + "\n".join(COMMANDS)
    )


async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    logger.info("chat.id=%s", chat_id)
    await update.message.reply_text(f"This chat's id is {chat_id}")
