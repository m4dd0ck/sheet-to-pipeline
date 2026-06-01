from pathlib import Path

from sheet_to_pipeline.legacy import DUPLICATED_MONTH
from sheet_to_pipeline.reconcile import compare, read_workbook_summary


def test_workbook_summary_is_read_by_month_label(built: tuple[Path, Path]) -> None:
    summary = read_workbook_summary(built[0])
    assert list(summary) == ["Jan 2024", "Feb 2024", "Mar 2024", "Apr 2024", "May 2024", "Jun 2024"]


def test_only_the_affected_months_differ(built: tuple[Path, Path]) -> None:
    checks = {c.month: c for c in compare(*built)}
    assert checks["2024-01"].status == checks["2024-02"].status == "match"
    march = checks[DUPLICATED_MONTH]
    assert {d.measure for d in march.differences} >= {"Revenue", "Units"}
    assert march.revenue_gap < 0  # the workbook counted the pasted-twice lines
    assert all(checks[m].revenue_gap > 0 for m in ("2024-04", "2024-05", "2024-06"))
