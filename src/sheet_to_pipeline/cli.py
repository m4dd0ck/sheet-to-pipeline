"""``s2p`` command line interface: the monthly routine, one command per step."""

import os
import subprocess
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from sheet_to_pipeline.extract import ExtractError, extract
from sheet_to_pipeline.legacy import build_legacy_workbook, write_month_csv
from sheet_to_pipeline.reconcile import compare, explain
from sheet_to_pipeline.report import write_excel_report

WORKBOOK = Path("legacy/Monthly Sales Report.xlsx")
INCOMING = Path("data/incoming")
DB = Path("output/sales.duckdb")
REPORT = Path("output/Monthly Sales Report.xlsx")
PROJECT_ROOT = Path(__file__).resolve().parents[2]

app = typer.Typer(help="Monthly sales report, rebuilt as a pipeline.", no_args_is_help=True)
console = Console()


@app.command()
def legacy(path: Annotated[Path, typer.Option(help="Where to write it.")] = WORKBOOK) -> None:
    """Write the original workbook (the "before")."""
    console.print(f"Legacy workbook: {build_legacy_workbook(path)}")


@app.command(name="new-month")
def new_month(month: Annotated[str, typer.Argument(help="YYYY-MM")] = "2024-07") -> None:
    """Drop a sample export for a new month into data/incoming, as the order system would."""
    console.print(f"New export: {write_month_csv(INCOMING / f'{month}.csv', month)}")


@app.command(name="extract")
def extract_command(workbook: Path = WORKBOOK, incoming: Path = INCOMING, db: Path = DB) -> None:
    """Load the workbook's raw tabs and any monthly CSVs into DuckDB."""
    try:
        counts = extract(workbook, incoming, db)
    except (ExtractError, FileNotFoundError) as error:
        raise typer.BadParameter(str(error)) from error
    console.print(", ".join(f"{name}: {count:,}" for name, count in counts.items()))


@app.command()
def run(db: Path = DB) -> None:
    """Build and test the dbt models."""
    result = subprocess.run(
        ["dbt", "build", "--profiles-dir", "."],
        cwd=PROJECT_ROOT,
        env={**os.environ, "S2P_DB_PATH": str(db.resolve())},
        check=False,
    )
    if result.returncode:
        raise typer.Exit(result.returncode)


@app.command()
def reconcile(workbook: Path = WORKBOOK, db: Path = DB) -> None:
    """Compare the workbook's Summary with the pipeline and explain each difference."""
    checks = explain(compare(workbook, db), db)
    table = Table(title="Workbook vs pipeline")
    for column in ("Month", "Status", "Revenue change", "Why"):
        table.add_column(column)
    for check in checks:
        colour = {"match": "green", "explained": "yellow"}.get(check.status, "red")
        why = " ".join(cause.summary for cause in check.causes)
        change = f"{check.revenue_gap:+,.2f}" if check.revenue_gap else ""
        table.add_row(check.label, f"[{colour}]{check.status}[/]", change, why)
    console.print(table)


@app.command()
def report(workbook: Path = WORKBOOK, db: Path = DB, out: Path = REPORT) -> None:
    """Write this month's report in the familiar Summary layout."""
    checks = explain(compare(workbook, db), db)
    console.print(f"Report: {write_excel_report(db, checks, out)}")


@app.command(name="all")
def run_all() -> None:
    """legacy, extract, run, reconcile and report, in order."""
    legacy()
    extract_command()
    run()
    reconcile()
    report()
