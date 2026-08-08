import logging
import os

import httpx
from telegram import Update
from telegram.ext import ContextTypes

from bot.api import fetch_recent_history

logger = logging.getLogger(__name__)

COMMAND_DESCRIPTIONS = [
    ("start", "Greet me and explain what I do"),
    ("help", "List available commands"),
    ("id", "Get this chat's id, for linking to a Nastolka location"),
    ("history", "Show the 5 most recent games logged for this location"),
]


def is_prod() -> bool:
    return os.environ.get("APP_ENV", "local").lower() == "prod"


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("chat.id=%s", update.effective_chat.id)
    await update.message.reply_text(
        "👋 I'm the Nastolka bot. I'll post here when a new game session is logged.\n"
        "Use /help to see what I can do."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("chat.id=%s", update.effective_chat.id)
    lines = [f"/{cmd} — {desc}" for cmd, desc in COMMAND_DESCRIPTIONS]
    await update.message.reply_text("Available commands:\n" + "\n".join(lines))


async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    logger.info("chat.id=%s", chat_id)
    await update.message.reply_text(f"This chat's id is {chat_id}")


async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    try:
        entries = await fetch_recent_history(chat_id)
    except httpx.HTTPError:
        logger.exception("Failed to fetch history for chat %s", chat_id)
        await update.message.reply_text("Couldn't reach Nastolka right now, try again later.")
        return

    if entries is None:
        await update.message.reply_text(
            "This chat isn't linked to a location yet. Send /id and set that as "
            "telegramChatId on a location."
        )
        return

    if not entries:
        await update.message.reply_text("No games logged yet for this location.")
        return

    lines = ["Recent games:"]
    for entry in entries:
        lines.append(f"• {format_entry(entry)}")

    text = "\n".join(lines)
    if not is_prod():
        text = f"🧪 [DEV]\n{text}"
    await update.message.reply_text(text)


def format_entry(entry: dict) -> str:
    game = entry.get("gameName") or "Unknown game"
    players = entry.get("players") or []
    if not players:
        return game

    names = ", ".join(format_player(player) for player in players)
    return f"{game} — {names}"


def format_player(player: dict) -> str:
    username = player.get("username", "?")
    placement = player.get("placement")
    return f"{username} (#{placement})" if placement else username
