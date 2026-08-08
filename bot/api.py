import os

import httpx


async def fetch_recent_history(chat_id: int) -> list[dict] | None:
    """Returns recent history entries for the location linked to chat_id, or None if no location is linked."""
    base_url = os.environ.get("NASTOLKA_API_BASE_URL", "http://localhost:8090")
    secret = os.environ.get("TELEGRAM_BOT_SECRET", "")

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{base_url}/api/telegram/history",
            params={"chatId": str(chat_id)},
            headers={"X-Telegram-Bot-Secret": secret},
        )

    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()
