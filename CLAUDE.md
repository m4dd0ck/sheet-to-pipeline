# sheet-to-pipeline: rules for agents

Read `README.md` for how it works, `RUNBOOK.md` for procedures, `TASK.md` for what is open.
Global rules in `~/.claude/CLAUDE.md` still apply.

- Public repo: no personal data, account figures, third-party names or the owner's email in any file; the git gate blocks them.
- Real-time commits only; never backdate, never set `GIT_AUTHOR_DATE`.
- Releases follow hq CONVENTIONS (`~/developer/hq/CONVENTIONS.md`); the RUNBOOK names the steps.
- Docs follow the four-file skeleton: a fact lives in one file, and the commands table is generated.
- Traps: the reconciliation figures in the README (March overstated, April to June understated) come from the generated data and change if `legacy.py` changes, keep them in step; a month in both the workbook and a CSV is refused on purpose, do not "fix" that; never commit `legacy/`, `data/`, `output/` or `site/`.
