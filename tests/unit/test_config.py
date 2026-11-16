"""Tests for lead_funnel.config."""

from __future__ import annotations

from pathlib import Path

import pytest

from lead_funnel.config import ConfigError, get_settings

LF_VARS = ("LF_SEED", "LF_SLA_MINUTES", "LF_DATA_DIR", "LF_DB_PATH", "LF_LOG_LEVEL")


def test_defaults_when_environment_is_empty() -> None:
    s = get_settings({})
    assert s.data_dir == Path("data")
    assert s.db_path == Path("data/warehouse/lead_funnel.duckdb")
    assert s.raw_dir == Path("data/raw")
    assert s.quarantine_dir == Path("data/quarantine")
    assert (s.seed, s.sla_minutes, s.log_level) == (42, 60, "INFO")


def test_environment_overrides_defaults() -> None:
    s = get_settings(
        {"LF_DATA_DIR": "/tmp/lf", "LF_SEED": "7", "LF_SLA_MINUTES": "30", "LF_LOG_LEVEL": "debug"}
    )
    assert s.data_dir == Path("/tmp/lf")
    assert s.db_path == Path("/tmp/lf/warehouse/lead_funnel.duckdb")  # follows data_dir
    assert (s.seed, s.sla_minutes, s.log_level) == (7, 30, "DEBUG")


def test_explicit_db_path_wins() -> None:
    assert get_settings({"LF_DB_PATH": "x.duckdb"}).db_path == Path("x.duckdb")


def test_blank_values_fall_back_to_defaults() -> None:
    s = get_settings({"LF_SEED": "  ", "LF_DATA_DIR": ""})
    assert (s.seed, s.data_dir) == (42, Path("data"))


@pytest.mark.parametrize(
    ("env", "message"),
    [
        ({"LF_SEED": "abc"}, "LF_SEED must be an integer"),
        ({"LF_SEED": "-1"}, "LF_SEED must be >= 0"),
        ({"LF_SLA_MINUTES": "0"}, "LF_SLA_MINUTES must be >= 1"),
        ({"LF_LOG_LEVEL": "LOUD"}, "LF_LOG_LEVEL must be one of"),
    ],
)
def test_invalid_values_raise_clear_errors(env: dict[str, str], message: str) -> None:
    with pytest.raises(ConfigError, match=message):
        get_settings(env)


def test_settings_are_immutable() -> None:
    s = get_settings({})
    with pytest.raises(AttributeError):
        s.seed = 1  # type: ignore[misc]


def test_env_file_is_loaded_but_does_not_override_real_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / ".env").write_text("LF_SEED=99\nLF_SLA_MINUTES=15\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    for var in LF_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("LF_SLA_MINUTES", "45")  # a real environment variable

    s = get_settings()
    assert s.seed == 99  # from .env
    assert s.sla_minutes == 45  # the real environment wins


def test_env_file_can_be_skipped(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / ".env").write_text("LF_SEED=99\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("LF_SEED", raising=False)
    assert get_settings(load_env_file=False).seed == 42
