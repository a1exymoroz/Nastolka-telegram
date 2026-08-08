import logging
import os

from dotenv import load_dotenv
from telegram import BotCommand
from telegram.ext import Application, CommandHandler

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


async def post_init(application: Application) -> None:
    await application.bot.set_my_commands(
        [BotCommand(cmd, desc) for cmd, desc in COMMAND_DESCRIPTIONS]
    )


def main() -> None:
    load_dotenv(".env.local")
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")

    application = Application.builder().token(token).post_init(post_init).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("id", id_command))
    application.add_handler(CommandHandler("history", history_command))

    webhook_url = os.environ.get("WEBHOOK_URL")
    if webhook_url:
        port = int(os.environ.get("PORT", "8080"))
        secret_token = os.environ.get("TELEGRAM_WEBHOOK_SECRET") or None
        logger.info("Nastolka bot starting (webhook on port %s)", port)
        application.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=token,
            webhook_url=f"{webhook_url.rstrip('/')}/{token}",
            secret_token=secret_token,
        )
    else:
        logger.info("Nastolka bot starting (long polling)")
        application.run_polling()


if __name__ == "__main__":
    main()
