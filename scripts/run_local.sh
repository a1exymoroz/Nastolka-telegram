#!/usr/bin/env bash
# Run the bot locally against .env.local (long polling, no public URL needed).
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -f .env.local ]; then
  echo ".env.local not found — copy .env.example to .env.local and fill it in first." >&2
  exit 1
fi

if [ ! -d .venv ]; then
  python -m venv .venv
fi

if [ -f .venv/bin/activate ]; then
  source .venv/bin/activate
else
  source .venv/Scripts/activate
fi

pip install -q -r requirements.txt
python -m bot.main
