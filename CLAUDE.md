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
2. **Create an issue** describing the work, add it to the `Nastolka` GitHub Project (owner
   `a1exymoroz`), and set its Sprint to the currently active iteration. None of the ids below
   are fixed — look each one up fresh, every time:
   ```bash
   # Project number, and the Sprint field's own id
   gh project list --owner a1exymoroz                       # find the Nastolka project's number
   gh project field-list <PROJECT_NUMBER> --owner a1exymoroz # find the "Sprint" field's id

   # Create the issue and add it to the project
   gh issue create --repo a1exymoroz/Nastolka-telegram \
     --title "..." --body "..." --project "Nastolka"

   # The currently active iteration (the one under "iterations", not "completedIterations")
   gh api graphql -f query='
   { node(id: "<SPRINT_FIELD_ID>") {
       ... on ProjectV2IterationField { configuration { iterations { id title startDate duration } } }
   } }'

   # The project's own node id, and the item id for the issue just created
   gh project view <PROJECT_NUMBER> --owner a1exymoroz --format json --jq .id
   gh project item-list <PROJECT_NUMBER> --owner a1exymoroz --limit 200 --format json \
     | python3 -c "
   import json, sys
   data = json.load(sys.stdin)
   for i in data['items']:
       c = i.get('content', {})
       if c.get('repository') == 'a1exymoroz/Nastolka-telegram' and c.get('number') == <ISSUE_NUMBER>:
           print(i['id'])
   "

   # Set the Sprint field on that item
   gh project item-edit --id <ITEM_ID> --field-id <SPRINT_FIELD_ID> \
     --project-id <PROJECT_NODE_ID> --iteration-id <ITERATION_ID>
   ```
   The Sprint field's id is stable across sprints, but the *iteration* id (which sprint is
   "current") is not — a new one is minted every time a new sprint starts, so always resolve it
   fresh via the GraphQL query rather than reusing a value from a previous session.
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
