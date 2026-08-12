import html
import logging
import os
from datetime import datetime, timezone
from functools import wraps

import httpx
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from bot.api import fetch_recent_history

logger = logging.getLogger(__name__)

COMMAND_DESCRIPTIONS = [
    ("start", "Greet me and explain what I do"),
    ("help", "List available commands"),
    ("id", "Get this chat's id, for linking to a Nastolka location"),
    ("history", "Show the 5 most recent games logged for this location"),
]

MAX_MESSAGE_AGE_SECONDS = 20  # headroom for scale-to-zero cold starts (e.g. Cloud Run)
MEDALS = {1: "🥇 ", 2: "🥈 ", 3: "🥉 "}


def is_prod() -> bool:
    return os.environ.get("APP_ENV", "local").lower() == "prod"


def skip_stale_messages(handler):
    """Ignore updates older than MAX_MESSAGE_AGE_SECONDS.

    On redeploy, Telegram delivers any backlog of queued updates (webhook
    retries or pending polling updates) all at once, which otherwise makes
    the bot reply to a burst of stale commands.
    """

    @wraps(handler)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        message = update.effective_message
        if message is not None and message.date is not None:
            age = (datetime.now(timezone.utc) - message.date).total_seconds()
            if age > MAX_MESSAGE_AGE_SECONDS:
                logger.info(
                    "Skipping stale update (age=%.1fs) chat.id=%s",
                    age,
                    update.effective_chat.id if update.effective_chat else None,
                )
                return
        await handler(update, context)

    return wrapper


@skip_stale_messages
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("chat.id=%s", update.effective_chat.id)
    await update.message.reply_text(
        "👋 I'm the Nastolka bot. I'll post here when a new game session is logged.\n"
        "Use /help to see what I can do."
    )


@skip_stale_messages
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("chat.id=%s", update.effective_chat.id)
    lines = [f"/{cmd} — {desc}" for cmd, desc in COMMAND_DESCRIPTIONS]
    await update.message.reply_text("Available commands:\n" + "\n".join(lines))


@skip_stale_messages
async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    logger.info("chat.id=%s", chat_id)
    await update.message.reply_text(f"This chat's id is {chat_id}")


@skip_stale_messages
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

    text = "🎲 <b>Recent games</b>\n\n" + "\n\n".join(format_entry(entry) for entry in entries)
    if not is_prod():
        text = f"🧪 [DEV]\n{text}"
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)


def format_entry(entry: dict) -> str:
    game = html.escape(entry.get("gameName") or "Unknown game")
    players = entry.get("players") or []

    lines = [f"<b>{game}</b>"]
    if players:
        lines.append(" · ".join(format_player(player) for player in players))

    link = history_link(entry)
    if link:
        lines.append(f'🔗 <a href="{html.escape(link)}">View details</a>')

    return "\n".join(lines)


def history_link(entry: dict) -> str | None:
    location_id = entry.get("locationId")
    history_id = entry.get("id")
    base_url = os.environ.get("WEBAPP_BASE_URL")
    if location_id is None or history_id is None or not base_url:
        return None

    return f"{base_url.rstrip('/')}/locations/{location_id}/history/{history_id}"


def format_player(player: dict) -> str:
    username = html.escape(player.get("username", "?"))
    placement = player.get("placement")
    prefix = MEDALS.get(placement, f"#{placement} " if placement else "")
    return f"{prefix}{username}"
