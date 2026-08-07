from telegram import Update
from telegram.ext import ContextTypes

COMMANDS = ["/start", "/help"]


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 I'm the Nastolka bot. I'll post here when a new game session is logged.\n"
        "Use /help to see what I can do."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Available commands:\n" + "\n".join(COMMANDS)
    )
