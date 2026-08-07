import logging
import os

from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler

from bot.handlers import help_command, id_command, start_command

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main() -> None:
    load_dotenv()
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")

    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("id", id_command))

    logger.info("Nastolka bot starting (long polling)")
    application.run_polling()


if __name__ == "__main__":
    main()
