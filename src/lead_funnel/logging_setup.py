"""Single place where logging is configured.

Modules never configure logging themselves; they only do::

    import logging
    logger = logging.getLogger(__name__)

and the application entry point (the CLI) calls :func:`configure_logging` once.
"""

from __future__ import annotations

import logging

LOG_FORMAT = "%(asctime)s %(levelname)-8s %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
_HANDLER_NAME = "lead_funnel_console"


def configure_logging(level: str = "INFO") -> None:
    """Set the root log level and attach one console handler.

    Idempotent: calling it again only changes the level and never adds a second
    handler. Handlers installed by others (e.g. pytest's ``caplog``) are left alone,
    unlike ``logging.basicConfig(force=True)``, which would remove them.
    """
    root = logging.getLogger()
    root.setLevel(level)
    if not any(h.get_name() == _HANDLER_NAME for h in root.handlers):
        handler = logging.StreamHandler()
        handler.set_name(_HANDLER_NAME)
        handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
        root.addHandler(handler)
