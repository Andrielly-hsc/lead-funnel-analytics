"""Command-line interface: ``lead-funnel <command>``.

Each sub-command is a thin wrapper: it parses arguments, loads settings and calls
functions from the package. Business logic never lives here.
"""

from __future__ import annotations

import argparse
import dataclasses
import logging
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from lead_funnel import __version__
from lead_funnel.config import ConfigError, Settings, get_settings
from lead_funnel.logging_setup import configure_logging

logger = logging.getLogger(__name__)

Handler = Callable[[argparse.Namespace, Settings], int]
ArgumentAdder = Callable[[argparse.ArgumentParser], None]


@dataclass(frozen=True)
class Command:
    help: str
    handler: Handler
    add_arguments: ArgumentAdder | None = None


def _not_implemented(task_id: str) -> Handler:
    """Placeholder handler for commands whose feature is not built yet."""

    def handler(args: argparse.Namespace, settings: Settings) -> int:
        logger.error("'%s' is not implemented yet (planned in %s).", args.command, task_id)
        return 1

    return handler


# ----------------------------------------------------------------------------------
# generate
# ----------------------------------------------------------------------------------
def _generate_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--seed", type=int, help="Random seed (default: LF_SEED).")
    parser.add_argument(
        "--n-leads", type=int, default=50_000, help="Number of unique leads (default: 50000)."
    )
    parser.add_argument("--clean", action="store_true", help="Do not inject data-quality issues.")
    parser.add_argument("--out-dir", type=Path, help="Output folder (default: <LF_DATA_DIR>/raw).")


def _generate(args: argparse.Namespace, settings: Settings) -> int:
    # imported here so `lead-funnel --help` stays fast (pandas/numpy load only when needed)
    from lead_funnel.generator.core import generate
    from lead_funnel.generator.params import GeneratorParams
    from lead_funnel.generator.writer import write_dataset

    if args.n_leads < 100:
        logger.error("--n-leads must be at least 100, got %d", args.n_leads)
        return 2
    seed = settings.seed if args.seed is None else args.seed
    out_dir = args.out_dir or settings.raw_dir
    gp = GeneratorParams()
    gp = dataclasses.replace(gp, volume=dataclasses.replace(gp.volume, n_leads=args.n_leads))

    logger.info("Generating %d leads (seed=%d, clean=%s)", args.n_leads, seed, args.clean)
    written = write_dataset(generate(gp, seed, clean=args.clean), out_dir)
    logger.info("Done: %d files in %s", len(written), out_dir)
    return 0


# ----------------------------------------------------------------------------------
# ingest
# ----------------------------------------------------------------------------------
def _ingest_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--full-refresh",
        action="store_true",
        help="Reload every file, even if it has not changed since the last load.",
    )
    parser.add_argument("--raw-dir", type=Path, help="Landing folder (default: <LF_DATA_DIR>/raw).")


def _ingest(args: argparse.Namespace, settings: Settings) -> int:
    from lead_funnel.ingestion.loaders import ingest

    raw_dir = args.raw_dir or settings.raw_dir
    if not raw_dir.is_dir():
        logger.error("Landing folder %s does not exist. Run `lead-funnel generate` first.", raw_dir)
        return 2
    results = ingest(raw_dir, settings.db_path, full_refresh=args.full_refresh)
    bad = [r for r in results if r.status in ("failed", "rejected")]
    logger.info(
        "Ingestion finished: %d loaded, %d skipped, %d rejected/failed -> %s",
        sum(r.status == "success" for r in results),
        sum(r.status == "skipped" for r in results),
        len(bad),
        settings.db_path,
    )
    return 1 if bad else 0


COMMANDS: dict[str, Command] = {
    "generate": Command(
        "Generate the synthetic CRM dataset into data/raw/", _generate, _generate_arguments
    ),
    "ingest": Command("Load landing files into the DuckDB raw layer", _ingest, _ingest_arguments),
    "profile": Command(
        "Profile raw data and build the quality scorecard", _not_implemented("F05-T01")
    ),
    "report": Command("Produce analysis figures and statistics", _not_implemented("F08")),
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
    for name, command in COMMANDS.items():
        sub = subparsers.add_parser(name, help=command.help, description=command.help)
        if command.add_arguments:
            command.add_arguments(sub)
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
    return COMMANDS[args.command].handler(args, settings)


if __name__ == "__main__":
    raise SystemExit(main())
