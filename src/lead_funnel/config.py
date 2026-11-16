"""Project settings, read from environment variables (12-factor app).

Every path and tunable parameter lives here, so no other module hard-codes them.
Values come from, in order of precedence:

1. real environment variables;
2. a local ``.env`` file (git-ignored; copy ``.env.example`` to start);
3. the defaults below.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

_LOG_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})


class ConfigError(ValueError):
    """Raised when an environment variable holds an invalid value."""


@dataclass(frozen=True)
class Settings:
    """Immutable project settings. Build it with :func:`get_settings`."""

    data_dir: Path
    db_path: Path
    seed: int
    sla_minutes: int
    log_level: str

    @property
    def raw_dir(self) -> Path:
        """Landing zone where the generator writes source files."""
        return self.data_dir / "raw"

    @property
    def quarantine_dir(self) -> Path:
        """Where ingestion moves files that break the data contract."""
        return self.data_dir / "quarantine"


def _read_int(env: Mapping[str, str], name: str, default: int, *, minimum: int) -> int:
    raw = env.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        value = int(raw)
    except ValueError:
        raise ConfigError(f"{name} must be an integer, got {raw!r}") from None
    if value < minimum:
        raise ConfigError(f"{name} must be >= {minimum}, got {value}")
    return value


def get_settings(env: Mapping[str, str] | None = None, *, load_env_file: bool = True) -> Settings:
    """Build :class:`Settings` from ``env`` (defaults to ``os.environ``).

    Passing ``env`` explicitly makes the function easy to test without touching the
    real environment.
    """
    if env is None:
        if load_env_file:
            # override=False: variables already set in the real environment always win.
            load_dotenv(dotenv_path=Path.cwd() / ".env", override=False)
        env = os.environ

    data_dir = Path(env.get("LF_DATA_DIR") or "data")
    db_path = Path(env.get("LF_DB_PATH") or data_dir / "warehouse" / "lead_funnel.duckdb")

    log_level = (env.get("LF_LOG_LEVEL") or "INFO").upper()
    if log_level not in _LOG_LEVELS:
        raise ConfigError(f"LF_LOG_LEVEL must be one of {sorted(_LOG_LEVELS)}, got {log_level!r}")

    return Settings(
        data_dir=data_dir,
        db_path=db_path,
        seed=_read_int(env, "LF_SEED", 42, minimum=0),
        sla_minutes=_read_int(env, "LF_SLA_MINUTES", 60, minimum=1),
        log_level=log_level,
    )
