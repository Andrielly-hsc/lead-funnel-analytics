"""Tests for lead_funnel.logging_setup."""

from __future__ import annotations

import logging

from lead_funnel.logging_setup import _HANDLER_NAME, configure_logging


def _our_handlers() -> list[logging.Handler]:
    return [h for h in logging.getLogger().handlers if h.get_name() == _HANDLER_NAME]


def test_configure_logging_is_idempotent() -> None:
    configure_logging("INFO")
    configure_logging("WARNING")
    assert len(_our_handlers()) == 1
    assert logging.getLogger().level == logging.WARNING


def test_configure_logging_keeps_foreign_handlers() -> None:
    foreign = logging.NullHandler()
    root = logging.getLogger()
    root.addHandler(foreign)
    try:
        configure_logging("INFO")
        assert foreign in root.handlers
    finally:
        root.removeHandler(foreign)
