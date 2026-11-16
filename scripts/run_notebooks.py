"""Execute the notebooks top to bottom and save them with their outputs.

    python scripts/run_notebooks.py           # execute and save notebooks/*.ipynb
    python scripts/run_notebooks.py --check   # execute only; fail on any error (CI)

A notebook that only runs in the author's session (hidden state, cells run out of
order) is not reproducible. Running every notebook from a fresh kernel, in order, is
the guarantee. Volatile metadata (execution timestamps) is not recorded, so a re-run
on the same data only changes the file if a result changed.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = ROOT / "notebooks"


def run(path: Path, *, save: bool) -> None:
    nb = nbformat.read(path, as_version=4)
    client = NotebookClient(
        nb,
        timeout=600,
        kernel_name="python3",
        record_timing=False,  # no per-cell timestamps -> clean diffs
        resources={"metadata": {"path": str(ROOT)}},  # run from the repo root, like the CLI
    )
    client.execute()
    if save:
        nb.metadata.pop("widgets", None)
        # nbformat.write() uses the platform line ending (CRLF on Windows); the repository
        # normalises to LF, so write the text ourselves
        text = nbformat.writes(nb)
        path.write_text(
            text if text.endswith("\n") else text + "\n", encoding="utf-8", newline="\n"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="execute without saving")
    args = parser.parse_args()
    for path in sorted(NOTEBOOKS.glob("*.ipynb")):
        run(path, save=not args.check)
        print(("ok    " if args.check else "wrote ") + str(path.relative_to(ROOT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
