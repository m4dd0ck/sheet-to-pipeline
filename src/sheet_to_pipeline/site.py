"""Before-and-after page for GitHub Pages, with both workbooks to download."""

import shutil
from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape

from sheet_to_pipeline.extract import extract
from sheet_to_pipeline.legacy import BUSINESS, SUMMARY_HEADER, build_legacy_workbook
from sheet_to_pipeline.pipeline import run_models
from sheet_to_pipeline.reconcile import compare, explain, pipeline_summary
from sheet_to_pipeline.report import write_excel_report

SITE_MARKER = ".s2p-site"
_env = Environment(
    loader=PackageLoader("sheet_to_pipeline", "templates"),
    autoescape=select_autoescape(["html", "j2"]),
)


class UnsafeOutputError(ValueError):
    """Raised instead of deleting a folder this tool did not create."""


def build_site(out_dir: Path) -> Path:
    """Run the whole flow in ``out_dir/work`` and write ``out_dir/index.html``."""
    if out_dir.exists():
        if any(out_dir.iterdir()) and not (out_dir / SITE_MARKER).exists():
            raise UnsafeOutputError(f"{out_dir} is not empty and was not built by s2p site")
        shutil.rmtree(out_dir)
    downloads = out_dir / "downloads"
    workbook = build_legacy_workbook(downloads / "Monthly Sales Report (before).xlsx")
    work = out_dir / "work"
    db_path = work / "sales.duckdb"
    extract(workbook, None, db_path)
    run_models(db_path, quiet=True)
    checks = explain(compare(workbook, db_path), db_path)
    write_excel_report(db_path, checks, downloads / "Monthly Sales Report (after).xlsx")
    summary = pipeline_summary(db_path)
    shutil.rmtree(work)

    causes = [cause for check in checks for cause in check.causes]
    html = _env.get_template("site.html.j2").render(
        business=BUSINESS,
        checks=checks,
        header=SUMMARY_HEADER,
        summary=[
            (label, [_cell(h, values[h]) for h in SUMMARY_HEADER[1:]])
            for label, (_, values) in summary.items()
        ],
        overstated=-sum(c.revenue_effect for c in causes if c.revenue_effect < 0),
        understated=sum(c.revenue_effect for c in causes if c.revenue_effect > 0),
    )
    (out_dir / "index.html").write_text(html, encoding="utf-8")
    (out_dir / SITE_MARKER).write_text("Built by s2p site; safe to delete.\n")
    return out_dir / "index.html"


def _cell(measure: str, value: float | str) -> str:
    """Display text for one Summary cell: counts whole, money to the cent, names as-is."""
    if isinstance(value, str):
        return value
    return f"{value:,.0f}" if measure in {"Units", "Invoices"} else f"{value:,.2f}"
