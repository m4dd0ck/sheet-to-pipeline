"""A new month arrives as a CSV drop and flows through with no code changes."""

import shutil
from pathlib import Path

import duckdb
from conftest import run_dbt

from sheet_to_pipeline.extract import extract
from sheet_to_pipeline.legacy import write_month_csv
from sheet_to_pipeline.reconcile import compare, explain


def test_csv_drop_becomes_a_new_month(built: tuple[Path, Path], tmp_path: Path) -> None:
    workbook = shutil.copy(built[0], tmp_path / built[0].name)
    write_month_csv(tmp_path / "incoming" / "2024-07.csv", "2024-07")
    db = tmp_path / "sales.duckdb"
    extract(Path(workbook), tmp_path / "incoming", db)
    run_dbt(db, tmp_path)

    with duckdb.connect(str(db), read_only=True) as connection:
        months = [
            r[0]
            for r in connection.execute("select month from marts.mart_monthly_summary").fetchall()
        ]
    assert months[-1] == "2024-07"

    checks = explain(compare(Path(workbook), db), db)
    july = checks[-1]
    assert july.status == "new" and july.causes == []
    assert [c.status for c in checks[:2]] == ["match", "match"]
