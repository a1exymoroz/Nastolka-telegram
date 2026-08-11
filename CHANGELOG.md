# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning follows
[Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.2] - 2026-08-11

### Added

- `CLAUDE.md`: documents the branch → issue (project + sprint) → PR workflow, and this
  versioning/changelog process.
- `CHANGELOG.md` (this file).

## [0.1.1] - 2026-08-11

### Added

- `docs/how-it-works.md`: marble-diagram walkthrough of the request flow, deploy flow, and
  budget-guard safety net.

## [0.1.0] - 2026-08-11

### Added

- Deploy to Google Cloud Run (webhook mode, scale-to-zero) as the production target,
  replacing the paid Northflank setup.
- GitHub Actions CI/CD (`.github/workflows/deploy.yml`): auto-deploys on every push to `main`
  via Workload Identity Federation — no downloaded service-account key.
- A ~$1-equivalent (4 PLN) billing budget with a `budget-guard` Cloud Function that scales the
  Cloud Run service to 0 instances if the cap is ever reached.
- `bot.__version__`, logged on startup, so a running deploy is identifiable from the logs.

### Changed

- Docker base image switched to `python:3.12-alpine` (~84MB, no compiler needed for any
  dependency).
- `MAX_MESSAGE_AGE_SECONDS` raised from 5s to 20s to tolerate Cloud Run cold starts without
  dropping a legitimate first message.
