"""Tests for the command-line interface."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from lead_funnel import __version__, cli

LF_VARS = ("LF_SEED", "LF_SLA_MINUTES", "LF_DATA_DIR", "LF_DB_PATH", "LF_LOG_LEVEL")


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


def test_unimplemented_command_points_to_its_task(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.ERROR):
        assert cli.main(["ingest"]) == 1
    assert "F03-T02" in caplog.text


def test_invalid_configuration_returns_exit_code_2(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setenv("LF_SEED", "not-a-number")
    with caplog.at_level(logging.ERROR):
        assert cli.main(["ingest"]) == 2
    assert "Invalid configuration" in caplog.text


def test_log_level_flag_overrides_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LF_LOG_LEVEL", "ERROR")
    cli.main(["--log-level", "debug", "ingest"])
    assert logging.getLogger().level == logging.DEBUG
