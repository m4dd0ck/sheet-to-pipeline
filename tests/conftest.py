import os
import subprocess
from pathlib import Path

import pytest

from sheet_to_pipeline.extract import extract
from sheet_to_pipeline.legacy import build_legacy_workbook

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def run_dbt(db_path: Path, workdir: Path) -> None:
    result = subprocess.run(
        [
            "dbt",
            "build",
            "--profiles-dir",
            ".",
            "--target-path",
            str(workdir / "target"),
            "--log-path",
            str(workdir / "logs"),
        ],  # fmt: skip
        cwd=PROJECT_ROOT,
        env={**os.environ, "S2P_DB_PATH": str(db_path)},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout[-3000:]


@pytest.fixture(scope="session")
def built(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Path]:
    """Legacy workbook plus a pipeline database built from it: (workbook, db)."""
    workdir = tmp_path_factory.mktemp("built")
    workbook = build_legacy_workbook(workdir / "Monthly Sales Report.xlsx")
    # Reason: dbt-duckdb views reference the catalog by file stem; keep the real name.
    db_path = workdir / "sales.duckdb"
    extract(workbook, None, db_path)
    run_dbt(db_path, workdir)
    return workbook, db_path
