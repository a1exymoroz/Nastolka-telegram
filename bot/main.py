import logging
import os

from dotenv import load_dotenv
from telegram import BotCommand, Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.request import HTTPXRequest

from bot import __version__
from bot.handlers import (
    COMMAND_DESCRIPTIONS,
    help_command,
    history_command,
    id_command,
    start_command,
)

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Cloud Run scales to zero between requests, so a cold container's first
# outbound connection to api.telegram.org can take longer than PTB's 5s
# default connect timeout.
TELEGRAM_CONNECT_TIMEOUT_SECONDS = 20.0


async def post_init(application: Application) -> None:
    await application.bot.set_my_commands(
        [BotCommand(cmd, desc) for cmd, desc in COMMAND_DESCRIPTIONS]
    )


async def error_handler(update: Update | None, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(
        "Unhandled exception while processing update=%s", update, exc_info=context.error
    )


def main() -> None:
    load_dotenv(".env.local")
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")

    request = HTTPXRequest(
        connect_timeout=TELEGRAM_CONNECT_TIMEOUT_SECONDS,
        read_timeout=TELEGRAM_CONNECT_TIMEOUT_SECONDS,
        write_timeout=TELEGRAM_CONNECT_TIMEOUT_SECONDS,
    )
    application = (
        Application.builder().token(token).request(request).post_init(post_init).build()
    )
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("id", id_command))
    application.add_handler(CommandHandler("history", history_command))
    application.add_error_handler(error_handler)

    webhook_url = os.environ.get("WEBHOOK_URL")
    if webhook_url:
        port = int(os.environ.get("PORT", "8080"))
        secret_token = os.environ.get("TELEGRAM_WEBHOOK_SECRET") or None
        logger.info("Nastolka bot version=%s starting (webhook on port %s)", __version__, port)
        application.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=token,
            webhook_url=f"{webhook_url.rstrip('/')}/{token}",
            secret_token=secret_token,
        )
    else:
        logger.info("Nastolka bot version=%s starting (long polling)", __version__)
        application.run_polling()


if __name__ == "__main__":
    main()
