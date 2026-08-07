# Nastolka Telegram Bot

Telegram bot companion for [Nastolka](https://github.com/a1exymoroz/Nastolka) ([issue #5](https://github.com/a1exymoroz/Nastolka/issues/5)).

Runs as its own long-lived process using long polling (no public URL/webhook needed). The Nastolka backend ([Nastolka-api](https://github.com/a1exymoroz/Nastolka-api)) sends game-session notifications to Telegram chats directly — this bot process only handles incoming commands, and shares the same bot token with the backend.

## Commands

- `/start` — greets the user and explains what the bot does
- `/help` — lists available commands
- `/id` — replies with the current chat's id, for linking it to a Nastolka location (see [Nastolka-api](https://github.com/a1exymoroz/Nastolka-api)'s "Telegram notifications" docs)
- `/history` — shows the 5 most recent games logged for the location linked to this chat

## Local setup

1. Create a bot via [@BotFather](https://t.me/BotFather) and copy the token it gives you (skip this if you already created one for [Nastolka-api](https://github.com/a1exymoroz/Nastolka-api)'s notifications — it's the same bot).
2. Copy `.env.example` to `.env.local` and set:
   - `TELEGRAM_BOT_TOKEN` — the bot's token
   - `TELEGRAM_BOT_SECRET` — shared secret for `/history`, must match `TELEGRAM_BOT_SECRET` in the backend's `.env.local`/`.env.prod`
   - `NASTOLKA_API_BASE_URL` — where the backend is running (defaults to `http://localhost:8090`)
   - `APP_ENV` — `local` (default) or `prod`. Since dev and prod currently share one bot token, `/history` replies (and, on the backend side, history-added notifications) are prefixed with `🧪 [DEV]` whenever this isn't `prod`, so you can tell which environment triggered a message.
3. Install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
4. Run the bot:
   ```bash
   python -m bot.main
   ```
5. Message the bot on Telegram and try `/start` and `/help`.

## Production

Deploy the `Dockerfile` as a second [Northflank](https://northflank.com/) service, alongside `Nastolka-api`:

1. In the same Northflank project, create a **Service** → source **Deployment**, build a Docker image from this repo, branch `main`, Dockerfile path `/Dockerfile`.
2. No public port mapping is needed — the bot only makes outbound requests (long polling), it doesn't listen for inbound traffic.
3. Set runtime environment variables `TELEGRAM_BOT_TOKEN`, `TELEGRAM_BOT_SECRET` (same values as configured on the `Nastolka-api` service), `NASTOLKA_API_BASE_URL` (the `Nastolka-api` service's public Northflank URL), and `APP_ENV=prod`.
4. Every push to `main` rebuilds and redeploys automatically, same as `Nastolka-api`.
