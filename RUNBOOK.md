# Runbook

Procedures for sheet-to-pipeline. `README.md` describes what each command does; this file says
when to run it and in what order.

## On open

```bash
git status --short
git log -3 --oneline
```

## On close

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src/
uv run pytest -q
```

## Monthly run

1. Drop the month's export into `data/incoming/` (or `uv run s2p new-month YYYY-MM` for a
   sample one).
2. `uv run s2p extract`, `uv run s2p run`, `uv run s2p reconcile`. The build fails on a line
   with no price in force, a line unaccounted for, or a summary that does not add up; fix the
   data or the price list, never the test.
3. `uv run s2p report` writes the Summary-layout workbook to `output/`. Read the Checks sheet.
4. Nothing is committed: inputs and outputs are gitignored.

## Release

Conventions in `~/developer/hq/CONVENTIONS.md` §Versioning.

1. Bump `version` in `pyproject.toml` and `__version__` in `src/sheet_to_pipeline/__init__.py`
   to the same value; `uv lock`.
2. Commit `chore: Release vX.Y.Z`, then `git tag -a vX.Y.Z -m "vX.Y.Z"` and
   `git push origin main --tags`.
3. `gh release create vX.Y.Z --title "sheet-to-pipeline vX.Y.Z" --notes "<what changed>"` with
   the compare link to the previous tag, marked latest.
4. CI must be green on the tagged commit. Nothing pins this package.

## Deploy

Nothing to do by hand: every push to `main` runs the full monthly flow in `ci.yml`, builds the
site (`s2p site`) and deploys it to GitHub Pages. A stale site means a red run: read the
Actions log. If Pages was never enabled, set the source to "GitHub Actions" once.

## Restore on a new machine

1. Clone `git@github.com:m4dd0ck/sheet-to-pipeline.git`; `uv sync`.
2. `uv run s2p all` regenerates the workbook, warehouse and report. No secrets, no data to
   fetch.

## Validate

```bash
uv run ruff check . && uv run ruff format --check .
uv run mypy src/
uv run pytest
uv run s2p all
uv run s2p site --out site
python3 ~/.claude/scripts/doc-check.py --repo .
```
