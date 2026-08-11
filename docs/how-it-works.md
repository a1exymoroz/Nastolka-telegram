# How it works

Three independent things happen in this system, on three different timescales: a Telegram
message gets answered (milliseconds to seconds), a push to `main` becomes a live deploy
(about a minute), and — hopefully never — a runaway bill gets shut off (hours). Each is
drawn below as a marble diagram: one horizontal line per actor, time flowing left to right,
`●` marking something happening.

## 1. A message getting answered

The bot runs on [Cloud Run](https://cloud.google.com/run) with `--min-instances 0`, so it
scales to zero when idle — no container, no cost — and starts one on demand.

```
Telegram    ──────●───────────────────────────────●──────────────────►
                 /start                          /help
                  │                                │
Cloud Run   ......│●━━━━━━━━━━━━━━━━━━━━━●.........│●─────────────────►
  instance        │  cold start (~5-8s)   idle→0    │ (already warm,
                  │                                 │  no cold start)
                  ▼                                 ▼
bot process  (booting: connect to Telegram,     (running, replies
              register commands, setWebhook)     immediately)
```

- `●` on the **Telegram** line = an update Telegram POSTs to the bot's webhook URL.
- `━━━` on the **Cloud Run instance** line = a container is up and serving.
- `.....` = scaled to zero — nothing running, nothing billed.

Sequence for a single `/start`, in more detail:

```mermaid
sequenceDiagram
    participant TG as Telegram
    participant CR as Cloud Run (nastolka-bot)
    participant Bot as bot/main.py + bot/handlers.py
    participant API as Nastolka-api

    TG->>CR: POST webhook path (contains bot token) — update: /start
    Note over CR: instance was at 0 → cold start
    CR->>Bot: run_webhook() delivers the update
    Bot->>Bot: skip_stale_messages() checks age under 20s
    Bot->>TG: sendMessage (reply)
    Note over Bot,API: /history instead calls fetch_recent_history()
    Bot->>API: GET recent games for this chat
    API-->>Bot: JSON entries
    Bot->>TG: sendMessage (formatted reply)
```

**Why `MAX_MESSAGE_AGE_SECONDS = 20`:** the [`skip_stale_messages`](../bot/handlers.py)
decorator drops any update older than that. It exists so that if the bot has been down for a
while, Telegram's replayed backlog of queued updates doesn't all get answered at once — but
20s also comfortably covers a normal cold start, so a real user's first message after idle
time still gets a reply.

## 2. A push to `main` becoming a live deploy

```
git push main   ──●──────────────────────────────────────────────►
                   │
GitHub Actions  ...│●━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━●...........►
                    │  auth (WIF) → upload source → Cloud Build →
                    │  deploy new revision              │
                    ▼                                    ▼
Cloud Run                                          new revision serving
                                                    100% of traffic
```

```mermaid
sequenceDiagram
    participant Dev as You (git push)
    participant GH as GitHub Actions
    participant WIF as Workload Identity Pool
    participant SA as github-deployer SA
    participant CB as Cloud Build
    participant CR as Cloud Run

    Dev->>GH: push to main
    GH->>WIF: present GitHub OIDC token
    WIF-->>GH: federated token (repo-scoped)
    GH->>SA: impersonate github-deployer
    SA-->>GH: short-lived access token
    GH->>CB: upload source, build image (Dockerfile)
    CB-->>CR: push built image
    GH->>CR: deploy new revision, shift 100% traffic
    CR-->>Bot: cold start, re-registers webhook with Telegram
```

No long-lived key ever leaves Google Cloud — [`.github/workflows/deploy.yml`](../.github/workflows/deploy.yml)
authenticates via [Workload Identity Federation](https://cloud.google.com/iam/docs/workload-identity-federation):
GitHub's own OIDC token is exchanged for permission to impersonate `github-deployer`, and that
exchange only works for pushes from `a1exymoroz/Nastolka-telegram` (enforced by the identity
pool's attribute condition), so no other repo can trigger a deploy with it.

## 3. The spend safety net

Independent of everything above — this doesn't touch the deploy flow or the bot process at all.

```
GCP billing   ──────────────────────●───────────────────────────────►
  (spend)                     crosses 4 PLN (~$1)
                                     │
Pub/Sub       ......................●......................► topic: billing-budget-alerts
                                     │
budget-guard  ......................●━━━━━━━━━►........................►
  function                          │  reads cost vs budget,
                                    │  patches Cloud Run service
                                    ▼
Cloud Run                    max-instances → 0
                              (service halts; nothing else touched)
```

```mermaid
sequenceDiagram
    participant Billing as Cloud Billing
    participant Budget as Budget (4 PLN, approx 1 USD)
    participant PS as Pub/Sub (billing-budget-alerts)
    participant Fn as budget-guard function
    participant CR as Cloud Run (nastolka-bot)

    Billing->>Budget: cost recalculated
    Budget->>PS: publish {costAmount, budgetAmount} (threshold crossed)
    PS->>Fn: trigger budget_guard()
    Fn->>Fn: cost >= budget?
    Fn->>CR: update_service(max_instance_count=0)
    Note over CR: no new instances start, service effectively paused
```

This only touches `nastolka-bot`'s max instance count — not the GCP project, not billing
itself, not the other infra (secrets, budget, function all keep running). To turn the bot back
on after investigating a spend spike:

```bash
gcloud run services update nastolka-bot --region us-central1 --max-instances=1
```

## Where things live

| Concern | Where |
|---|---|
| Bot code | [`bot/`](../bot/) |
| Container build | [`Dockerfile`](../Dockerfile), [`.dockerignore`](../.dockerignore) |
| Deploy workflow | [`.github/workflows/deploy.yml`](../.github/workflows/deploy.yml) |
| Manual deploy steps, env vars | [`README.md`](../README.md) |
| Secrets | GCP Secret Manager (`telegram-bot-token`, `telegram-bot-secret`, `telegram-webhook-secret`) — not in this repo |
| Budget + auto-stop function | GCP project `nastolka-bot` (Billing Budgets, Pub/Sub, Cloud Functions) — not in this repo |
