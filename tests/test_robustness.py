"""Real exports are messy; every problem must come back as a clear ExtractError."""

from pathlib import Path

import pytest
from openpyxl import load_workbook

from sheet_to_pipeline.extract import ExtractError, extract
from sheet_to_pipeline.legacy import RAW_HEADER
from sheet_to_pipeline.reconcile import MonthCheck
from sheet_to_pipeline.report import write_excel_report

HEADER = ",".join(RAW_HEADER)


def drop(tmp_path: Path, name: str, body: str | bytes) -> Path:
    incoming = tmp_path / "incoming"
    incoming.mkdir(exist_ok=True)
    path = incoming / name
    if isinstance(body, bytes):
        path.write_bytes(body)
    else:
        path.write_text(body)
    return incoming


@pytest.mark.parametrize(
    ("body", "message"),
    [
        ("", "empty"),
        (f"{HEADER}\n2024-07-02,INV-1,Cafe,BR-01\n", "expected 6 columns"),
        (f"{HEADER}\n2024-07-02,INV-1,Cafe,BR-01,lots,R01\n", "row 2"),
        (f"{HEADER}\n2024-07-02,INV-1,Cafe,BR-01,2.5,R01\n", "not a whole number"),
        (f"{HEADER}\n07/02/2024,INV-1,Cafe,BR-01,2,R01\n", "not YYYY-MM-DD"),
        (f"{HEADER}\n2024-06-30,INV-1,Cafe,BR-01,2,R01\n", "outside 2024-07"),
    ],
)
def test_bad_drops_are_explained(
    built: tuple[Path, Path], tmp_path: Path, body: str, message: str
) -> None:
    incoming = drop(tmp_path, "2024-07.csv", body)
    with pytest.raises(ExtractError, match=message):
        extract(built[0], incoming, tmp_path / "db.duckdb")


def test_windows_encoded_export_is_read(built: tuple[Path, Path], tmp_path: Path) -> None:
    body = f"{HEADER}\n2024-07-02,INV-1,Café Crème,BR-01,2.0,R01\n".encode("cp1252")
    counts = extract(built[0], drop(tmp_path, "2024-07.csv", body), tmp_path / "db.duckdb")
    assert counts["sales_lines"] > 0


def test_formula_like_text_stays_text_in_the_report(
    built: tuple[Path, Path], tmp_path: Path
) -> None:
    import duckdb

    db = tmp_path / "sales.duckdb"
    with duckdb.connect(str(db)) as connection:
        connection.execute("create schema marts")
        connection.execute(
            "create table marts.mart_monthly_summary as select '2024-01' as month, 'Jan 2024' as "
            "month_label, 1.0 as revenue, 1 as units, 1 as invoices, 1.0 as avg_invoice, "
            "1.0 as north, 0.0 as south, 0.0 as central, '=HYPERLINK(\"http://x\")' as top_rep"
        )
    path = write_excel_report(db, [MonthCheck("2024-01", "Jan 2024")], tmp_path / "r.xlsx")
    cell = load_workbook(path)["Summary"]["I5"]
    assert cell.data_type == "s"
