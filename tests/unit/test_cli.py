"""Tests for the command-line interface."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from lead_funnel import __version__, cli

LF_VARS = (
    "LF_SEED",
    "LF_SLA_MINUTES",
    "LF_DATA_DIR",
    "LF_DB_PATH",
    "LF_LOG_LEVEL",
    "LF_REPORTS_DIR",
)


@pytest.fixture(autouse=True)
def _isolated_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Run every CLI test in an empty folder with no LF_* variables (no stray .env)."""
    monkeypatch.chdir(tmp_path)
    for var in LF_VARS:
        monkeypatch.delenv(var, raising=False)


def test_help_lists_all_commands(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        cli.main(["--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    for command in ("generate", "ingest", "profile", "report"):
        assert command in out


def test_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        cli.main(["--version"])
    assert __version__ in capsys.readouterr().out


def test_command_is_required() -> None:
    with pytest.raises(SystemExit) as exc:
        cli.main([])
    assert exc.value.code == 2


def test_invalid_configuration_returns_exit_code_2(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setenv("LF_SEED", "not-a-number")
    with caplog.at_level(logging.ERROR):
        assert cli.main(["profile"]) == 2
    assert "Invalid configuration" in caplog.text


def test_log_level_flag_overrides_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LF_LOG_LEVEL", "ERROR")
    cli.main(["--log-level", "debug", "profile"])
    assert logging.getLogger().level == logging.DEBUG


def test_generate_writes_the_landing_zone(tmp_path: Path) -> None:
    out = tmp_path / "raw"
    code = cli.main(["generate", "--seed", "3", "--n-leads", "300", "--out-dir", str(out)])
    assert code == 0
    for name in ("leads.csv", "interactions.jsonl", "agents.parquet", "_manifest.json"):
        assert (out / name).exists()


def test_generate_rejects_tiny_datasets(tmp_path: Path) -> None:
    assert cli.main(["generate", "--n-leads", "5", "--out-dir", str(tmp_path)]) == 2


def test_report_needs_a_warehouse(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LF_DATA_DIR", str(tmp_path / "nothing"))
    assert cli.main(["report", "--seeds", "0"]) == 2
