# Nastolka Telegram Bot

Telegram bot companion for [Nastolka](https://github.com/a1exymoroz/Nastolka) ([issue #5](https://github.com/a1exymoroz/Nastolka/issues/5)).

Runs as its own long-lived process. It receives commands via webhook when `WEBHOOK_URL` is set (production), and falls back to long polling when it isn't (local dev, no public URL needed). The Nastolka backend ([Nastolka-api](https://github.com/a1exymoroz/Nastolka-api)) sends game-session notifications to Telegram chats directly — this bot process only handles incoming commands, and shares the same bot token with the backend.

On startup the bot also registers its command list with Telegram (`set_my_commands`), so they show up with descriptions when a user types `/` in the chat.

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
   - `WEBHOOK_URL`, `PORT`, `TELEGRAM_WEBHOOK_SECRET` — leave these unset for local dev; the bot uses long polling when `WEBHOOK_URL` is empty. See Production below.
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

Deployed to [Google Cloud Run](https://cloud.google.com/run) — a free, scale-to-zero container host well suited to this bot's low, bursty traffic (idle time costs nothing; this workload stays well within the monthly free tier).

1. One-time setup: a GCP project with billing enabled (required by Cloud Run even though usage stays free), with `run.googleapis.com`, `cloudbuild.googleapis.com`, and `secretmanager.googleapis.com` enabled, and `TELEGRAM_BOT_TOKEN` / `TELEGRAM_BOT_SECRET` / `TELEGRAM_WEBHOOK_SECRET` stored in Secret Manager.
2. Deploy straight from source (Cloud Build uses the repo's `Dockerfile`):
   ```bash
   gcloud run deploy nastolka-bot \
     --source . \
     --region us-central1 \
     --allow-unauthenticated \
     --port 8080 \
     --min-instances 0 --max-instances 1 \
     --memory 256Mi --cpu 1 \
     --set-env-vars APP_ENV=prod,NASTOLKA_API_BASE_URL=<Nastolka-api public URL> \
     --set-secrets TELEGRAM_BOT_TOKEN=telegram-bot-token:latest,TELEGRAM_BOT_SECRET=telegram-bot-secret:latest,TELEGRAM_WEBHOOK_SECRET=telegram-webhook-secret:latest
   ```
   `bot.__version__` (in `bot/__init__.py`) is logged on startup (`Nastolka bot version=<version> starting...`) so you can tell from the logs which release is running — bump it by hand when you cut a new release.
   `--allow-unauthenticated` is required since Telegram calls the webhook with no GCP credentials — request authenticity instead relies on the bot token embedded in the URL path plus the `TELEGRAM_WEBHOOK_SECRET` header check (see `bot/main.py`).
3. Grab the assigned URL and set it as `WEBHOOK_URL` so the bot switches into webhook mode and self-registers with Telegram on next boot (via `run_webhook` — no manual `setWebhook` call needed):
   ```bash
   URL=$(gcloud run services describe nastolka-bot --region us-central1 --format "value(status.url)")
   gcloud run services update nastolka-bot --region us-central1 \
     --set-env-vars WEBHOOK_URL=$URL,APP_ENV=prod,NASTOLKA_API_BASE_URL=<Nastolka-api public URL>
   ```
4. Every push to `main` redeploys automatically via `.github/workflows/deploy.yml`, which builds and deploys straight from source using [Workload Identity Federation](https://cloud.google.com/iam/docs/workload-identity-federation) — GitHub Actions impersonates a dedicated `github-deployer` service account with no downloaded key file. The provider's attribute condition restricts impersonation to this exact repo. Config lives in repo variables (`GCP_PROJECT_ID`, `GCP_WIF_PROVIDER`, `GCP_DEPLOYER_SA`, `CLOUD_RUN_URL`, `NASTOLKA_API_BASE_URL`).

Note: with `--min-instances 0`, the very first request after an idle period pays a cold-start cost; `MAX_MESSAGE_AGE_SECONDS` in `bot/handlers.py` is set high enough to tolerate that without dropping the message.

There's also a $1-equivalent (4 PLN) billing budget on the project with a `budget-guard` Cloud Function that scales the service to 0 instances if it's ever reached, as a spend safety net independent of this deploy flow.
