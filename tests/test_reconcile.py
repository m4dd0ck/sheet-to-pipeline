from pathlib import Path

from sheet_to_pipeline.legacy import DUPLICATED_MONTH
from sheet_to_pipeline.reconcile import compare, explain, read_workbook_summary


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


def test_every_revenue_gap_is_fully_explained(built: tuple[Path, Path]) -> None:
    checks = explain(compare(*built), built[1])
    assert all(check.status in {"match", "explained"} for check in checks)
    march = next(c for c in checks if c.month == DUPLICATED_MONTH)
    assert [c.kind for c in march.causes] == ["repeated_paste"]
    assert "rows" in march.causes[0].evidence[0]
    april = next(c for c in checks if c.month == "2024-04")
    assert [c.kind for c in april.causes] == ["stale_price"]
    assert len(april.causes[0].evidence) == 3  # the three products whose price changed
