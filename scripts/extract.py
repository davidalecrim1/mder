#!/usr/bin/env python3
"""
Extract text from a document file for mder processing.
Backward-compatible entrypoint wrapper.
"""

import os
import sys

# Force UTF-8 stdout/stderr so the dependency-check glyphs (✓ / ✗) don't raise
# UnicodeEncodeError on Windows consoles that default to a legacy code page
# (e.g. GBK / cp936).
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

# Ensure the project root directory (where the 'mder' package lives) is in sys.path
# so the modular package can be imported reliably regardless of the working directory.
sys.path.insert(0, str(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def _standalone_check() -> None:
    """Lightweight, self-contained dependency report.

    Used only when the `mder` package isn't importable — e.g. when this file is
    run straight from its raw URL to validate a machine before installing:

        curl -fsSL .../scripts/extract.py | python3 - --check

    Installed runs use the package's canonical report instead (see below).
    """
    import importlib.util
    import shutil

    groups = [
        ("PDF (text-heavy)", ["pypdf", "pdfminer"],
         [("pdftotext", "poppler-utils")], "any one of pdftotext / pypdf / pdfminer is enough"),
        ("PDF (technical: tables, code, formulas)", ["docling"], [],
         "needed only for --mode technical; otherwise falls back to the text chain"),
        ("EPUB", ["ebooklib", "bs4"], [], "falls back to a stdlib zipfile parser if missing"),
        ("DOCX", ["docx"], [], "falls back to a stdlib ZIP/XML parser if missing"),
        ("HTML", ["bs4"], [], "falls back to the stdlib html.parser if missing"),
        ("RTF", ["striprtf"], [], "falls back to a basic regex cleanup if missing"),
        ("MOBI / AZW / AZW3", [], [("ebook-convert", "Calibre")],
         "Calibre is required for these formats — no fallback"),
    ]
    print("mder — dependency check\n")
    for label, modules, tools, note in groups:
        print(f"  {label}")
        for mod in modules:
            ok = importlib.util.find_spec(mod) is not None
            print(f"      {'✓' if ok else '✗'} python: {mod}")
        for cmd, pkg in tools:
            ok = shutil.which(cmd) is not None
            print(f"      {'✓' if ok else '✗'} system: {cmd} ({pkg})")
        print(f"      → {note}")
    print(
        "\nMissing Python packages are optional — most formats fall back to a "
        "stdlib parser. Calibre is the only hard requirement, and only for MOBI/AZW."
    )


if __name__ == "__main__":
    if "--check" in sys.argv[1:]:
        try:
            from mder.cli import main  # installed: canonical, richer report
        except ImportError:
            _standalone_check()        # standalone: run from a raw URL, no package
            sys.exit(0)
        main()
    else:
        from mder.cli import main
        main()
