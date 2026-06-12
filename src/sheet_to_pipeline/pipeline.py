"""Run the dbt project against a given DuckDB file."""

import os
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class ModelBuildError(RuntimeError):
    """Raised when dbt build fails; carries the tail of dbt's output."""


def run_models(db_path: Path, quiet: bool = False) -> None:
    """``dbt build`` (models and tests) into ``db_path``."""
    result = subprocess.run(
        # Reason: partial parsing cached across different database paths caused spurious
        # "unable to infer dependencies" errors; a full parse costs about a second.
        ["dbt", "build", "--profiles-dir", ".", "--no-partial-parse"],
        cwd=PROJECT_ROOT,
        env={**os.environ, "S2P_DB_PATH": str(db_path.resolve())},
        capture_output=quiet,
        text=True,
        check=False,
    )
    if result.returncode:
        raise ModelBuildError((result.stdout or "")[-3000:] or "dbt build failed")
