from pathlib import Path

import duckdb
import pytest

from sheet_to_pipeline.extract import ExtractError, extract
from sheet_to_pipeline.legacy import build_legacy_workbook, month_lines, write_month_csv


@pytest.fixture(scope="module")
def workbook(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return build_legacy_workbook(tmp_path_factory.mktemp("legacy") / "report.xlsx")


def test_every_pasted_row_is_loaded_with_its_origin(workbook: Path, tmp_path: Path) -> None:
    db = tmp_path / "s2p.duckdb"
    counts = extract(workbook, None, db)
    pasted = sum(len(lines) for lines in month_lines().values()) + 25
    assert counts == {"sales_lines": pasted, "products": 21, "reps": 5}
    with duckdb.connect(str(db), read_only=True) as connection:
        row = connection.execute(
            "select source, source_row from raw.sales_lines where month = '2024-03' "
            "order by source_row desc limit 1"
        ).fetchone()
    assert row is not None and row[0] == "Raw - 2024-03"


def test_monthly_csv_drop_is_added(workbook: Path, tmp_path: Path) -> None:
    write_month_csv(tmp_path / "incoming" / "2024-07.csv", "2024-07")
    counts = extract(workbook, tmp_path / "incoming", tmp_path / "s2p.duckdb")
    base = sum(len(lines) for lines in month_lines().values()) + 25
    assert counts["sales_lines"] > base


def test_a_month_in_two_sources_is_refused(workbook: Path, tmp_path: Path) -> None:
    write_month_csv(tmp_path / "incoming" / "2024-06.csv", "2024-06")
    with pytest.raises(ExtractError, match="2024-06"):
        extract(workbook, tmp_path / "incoming", tmp_path / "s2p.duckdb")


def test_wrong_columns_are_refused(workbook: Path, tmp_path: Path) -> None:
    (tmp_path / "incoming").mkdir()
    (tmp_path / "incoming" / "2024-07.csv").write_text("Date,Invoice,Amount\n2024-07-01,A,5\n")
    with pytest.raises(ExtractError, match="expected columns"):
        extract(workbook, tmp_path / "incoming", tmp_path / "s2p.duckdb")
