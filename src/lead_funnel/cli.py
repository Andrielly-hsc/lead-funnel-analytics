"""Command-line interface: ``lead-funnel <command>``.

Each sub-command is a thin wrapper: it parses arguments, loads settings and calls
functions from the package. Business logic never lives here.
"""

from __future__ import annotations

import argparse
import logging
from collections.abc import Callable, Sequence

from lead_funnel import __version__
from lead_funnel.config import ConfigError, Settings, get_settings
from lead_funnel.logging_setup import configure_logging

logger = logging.getLogger(__name__)

Handler = Callable[[argparse.Namespace, Settings], int]


def _not_implemented(task_id: str) -> Handler:
    """Placeholder handler for commands whose feature is not built yet."""

    def handler(args: argparse.Namespace, settings: Settings) -> int:
        logger.error("'%s' is not implemented yet (planned in %s).", args.command, task_id)
        return 1

    return handler


# command name -> (help text, handler)
COMMANDS: dict[str, tuple[str, Handler]] = {
    "generate": ("Generate the synthetic CRM dataset into data/raw/", _not_implemented("F02-T05")),
    "ingest": ("Load landing files into the DuckDB raw layer", _not_implemented("F03-T02")),
    "profile": ("Profile raw data and build the quality scorecard", _not_implemented("F05-T01")),
    "report": ("Produce analysis figures and statistics", _not_implemented("F08")),
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lead-funnel",
        description="Lead funnel analytics pipeline.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--log-level",
        help="Override LF_LOG_LEVEL (DEBUG, INFO, WARNING, ERROR).",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="<command>", required=True)
    for name, (help_text, _) in COMMANDS.items():
        subparsers.add_parser(name, help=help_text, description=help_text)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        settings = get_settings()
    except ConfigError as exc:
        configure_logging("ERROR")
        logger.error("Invalid configuration: %s", exc)
        return 2

    configure_logging((args.log_level or settings.log_level).upper())
    logger.debug("Settings: %s", settings)
    _, handler = COMMANDS[args.command]
    return handler(args, settings)


if __name__ == "__main__":
    raise SystemExit(main())
