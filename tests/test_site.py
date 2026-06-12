from pathlib import Path

import pytest

from sheet_to_pipeline.site import UnsafeOutputError, build_site


def test_site_has_page_and_both_workbooks(tmp_path: Path) -> None:
    index = build_site(tmp_path / "site")
    html = index.read_text()
    assert "25 lines were pasted twice" in html
    assert "Sourdough loaf" in html
    downloads = sorted(p.name for p in (tmp_path / "site" / "downloads").iterdir())
    assert downloads == ["Monthly Sales Report (after).xlsx", "Monthly Sales Report (before).xlsx"]


def test_site_refuses_to_replace_an_unrelated_folder(tmp_path: Path) -> None:
    (tmp_path / "notes.txt").write_text("keep me")
    with pytest.raises(UnsafeOutputError):
        build_site(tmp_path)
    assert (tmp_path / "notes.txt").exists()
