# Working in this repo

## Starting new work

Every piece of new work (a new chat, a new task) follows this order — branch, then issue,
then implementation, then PR:

1. **Branch from `main`** — always sync first:
   ```bash
   git fetch origin
   git checkout main
   git merge --ff-only origin/main
   git checkout -b <type>/<short-description>   # feature/, fix/, docs/, chore/
   ```
2. **Create an issue** describing the work, add it to the `Nastolka` GitHub Project, and set
   its Sprint to the currently active iteration:
   ```bash
   gh issue create --repo a1exymoroz/Nastolka-telegram \
     --title "..." --body "..." --project "Nastolka"
   ```
   Then set the Sprint field (a `ProjectV2IterationField`, so it needs the project item id,
   not the issue number):
   ```bash
   # Find the item id for the issue you just created
   gh project item-list 3 --owner a1exymoroz --limit 200 --format json \
     | python3 -c "
   import json, sys
   data = json.load(sys.stdin)
   for i in data['items']:
       c = i.get('content', {})
       if c.get('repository') == 'a1exymoroz/Nastolka-telegram' and c.get('number') == <ISSUE_NUMBER>:
           print(i['id'])
   "

   # Find the currently active iteration id (the one under "iterations", not "completedIterations")
   gh api graphql -f query='
   { node(id: "PVTIF_lAHOAbKo9c4Be-ouzhaQ2Lc") {
       ... on ProjectV2IterationField { configuration { iterations { id title startDate duration } } }
   } }'

   # Set it
   gh project item-edit --id <ITEM_ID> \
     --field-id "PVTIF_lAHOAbKo9c4Be-ouzhaQ2Lc" \
     --project-id "PVT_kwHOAbKo9c4Be-ou" \
     --iteration-id <ITERATION_ID>
   ```
   (Project `Nastolka` = project number 3, owner `a1exymoroz`, node id
   `PVT_kwHOAbKo9c4Be-ou`. `PVTIF_lAHOAbKo9c4Be-ouzhaQ2Lc` identifies the Sprint *field*
   itself and is stable — but the *iteration* id (e.g. `13a60aa3` for "Sprint 2") is **not**
   fixed: a new one is minted every time a new sprint starts, so always look it up fresh with
   the GraphQL query above rather than reusing an old value.)
3. **Do the work** on the branch, committing normally.
4. **Open a PR** against `main` that references the issue (e.g. `Closes #<N>` in the body), via
   `gh pr create`.

This applies to Claude Code sessions in this repo just as much as to manual work — don't
commit straight to `main`, and don't skip the issue.

## Versioning and changelog

- The release version lives in `bot/__init__.py` as `__version__`, follows
  [semver](https://semver.org/), and is logged on every startup (see `bot/main.py`) so a
  running Cloud Run revision's logs identify exactly which release it is.
- Every PR merged to `main` bumps `__version__` (patch for fixes/chores/docs, minor for new
  features, major for breaking changes) and adds a matching entry to `CHANGELOG.md`
  ([Keep a Changelog](https://keepachangelog.com/) format).
- Don't skip the bump on docs-only or process-only PRs — the point is that any merge to `main`
  is traceable in the logs to a `CHANGELOG.md` entry, not just behavioral changes.
