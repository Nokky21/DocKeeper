"""Línea de órdenes de DocKeeper."""

from __future__ import annotations

import argparse
from typing import List, Optional

from dockeeper import __version__


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="dockeeper")
    parser.add_argument("--version", action="version", version=f"dockeeper {__version__}")
    parser.parse_args(argv)
    return 0
