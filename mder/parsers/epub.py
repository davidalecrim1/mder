from __future__ import annotations

import posixpath
import re
import zipfile
import sys
from mder.parsers.html import _HTMLTextExtractor


def extract_sections_with_ebooklib(epub_path: str) -> list[str] | None:
    """Return one text block per spine document, in reading order.

    Iterating the spine (not `get_items_of_type`) preserves the book's own
    reading order, so each block corresponds to a table-of-contents section.
    """
    try:
        import ebooklib
        from ebooklib import epub
        from bs4 import BeautifulSoup

        book = epub.read_epub(epub_path)
        by_id = {item.get_id(): item for item in book.get_items()}
        sections: list[str] = []
        used: set = set()
        seen_text: set = set()

        def _add(item):
            text = BeautifulSoup(item.get_content(), "html.parser").get_text(
                separator="\n"
            )
            fingerprint = " ".join(text.split())  # ignore whitespace differences
            if fingerprint and fingerprint not in seen_text:
                seen_text.add(fingerprint)
                sections.append(text)

        for entry in book.spine:
            idref = entry[0] if isinstance(entry, (list, tuple)) else entry
            item = by_id.get(idref)
            if item is None or item.get_type() != ebooklib.ITEM_DOCUMENT:
                continue
            _add(item)
            used.add(idref)
        # Safety net: append any content document not referenced by the spine, so
        # a malformed or unusual EPUB never loses text. Prioritising completeness
        # over de-duplication — `_add` only skips byte-identical repeats, so an
        # extra copy of a section is preferred to any risk of a cut-off chapter.
        for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            if item.get_id() not in used:
                _add(item)
        return sections or None
    except ImportError:
        return None
    except Exception as e:
        print(f"  [warn] extract_with_ebooklib failed: {type(e).__name__}: {e}", file=sys.stderr)
        return None


def extract_with_ebooklib(epub_path: str) -> str | None:
    sections = extract_sections_with_ebooklib(epub_path)
    return "\n\n".join(sections) if sections else None


def _find_opf_path(zf: zipfile.ZipFile) -> str | None:
    """Locate the OPF package document inside an EPUB archive.

    First tries ``META-INF/container.xml`` (the spec-defined entry point),
    then falls back to scanning the archive for any ``.opf`` file.
    """
    # Spec-defined: read container.xml for the rootfile path
    try:
        container = zf.read("META-INF/container.xml").decode("utf-8", errors="replace")
        match = re.search(r'full-path=["\']([^"\']+\.opf)["\']', container)
        if match:
            return match.group(1)
    except (KeyError, Exception):
        pass

    # Fallback: glob for any .opf file
    opf_files = [n for n in zf.namelist() if n.endswith(".opf")]
    return opf_files[0] if opf_files else None


def extract_with_zipfile(epub_path: str) -> str | None:
    sections = extract_sections_with_zipfile(epub_path)
    return "\n\n".join(sections) if sections else None


def extract_sections_with_zipfile(epub_path: str) -> list[str] | None:
    """stdlib-only EPUB extractor: unzip → parse HTML files in spine order,
    returning one text block per document (a table-of-contents section)."""
    try:
        with zipfile.ZipFile(epub_path) as zf:
            names = zf.namelist()

            # Locate OPF and determine its directory for resolving relative hrefs
            opf_path = _find_opf_path(zf)
            opf_dir = posixpath.dirname(opf_path) if opf_path else ""

            # Build reading order from the OPF spine (not the manifest's href
            # order), then append any remaining content docs as a safety net.
            spine_order: list[str] = []
            seen: set[str] = set()
            if opf_path:
                opf_text = zf.read(opf_path).decode("utf-8", errors="replace")

                # Manifest: item id -> resolved href. Parse each <item> opening
                # tag so attribute order (id before/after href) does not matter;
                # both self-closing <item .../> and <item ...></item> forms work
                # because all attributes live in the opening tag.
                manifest: dict[str, str] = {}
                for item_tag in re.findall(r"<item\b[^>]*?/?>", opf_text):
                    id_m = re.search(r'\bid=["\']([^"\']+)["\']', item_tag)
                    href_m = re.search(r'\bhref=["\']([^"\']+)["\']', item_tag)
                    if id_m and href_m:
                        href = href_m.group(1)
                        resolved = posixpath.normpath(posixpath.join(opf_dir, href)) if opf_dir else href
                        manifest[id_m.group(1)] = resolved

                # Spine: ordered idrefs -> hrefs (true reading order).
                for idref in re.findall(r'<itemref\b[^>]*?\bidref=["\']([^"\']+)["\']', opf_text):
                    href = manifest.get(idref)
                    if href and href not in seen:
                        spine_order.append(href)
                        seen.add(href)

                # Safety net: append remaining manifest content documents (e.g. a
                # nav doc not in the spine) in manifest order, so nothing is lost.
                for href in manifest.values():
                    if href.endswith((".html", ".xhtml")) and href not in seen:
                        spine_order.append(href)
                        seen.add(href)

            html_files = spine_order or sorted(
                n for n in names if n.endswith((".html", ".xhtml"))
            )
            if not html_files:
                return None

            parts = []
            for name in html_files:
                try:
                    raw = zf.read(name).decode("utf-8", errors="replace")
                    parser = _HTMLTextExtractor()
                    parser.feed(raw)
                    parts.append(parser.get_text())
                except Exception:
                    continue
            return parts or None
    except Exception as e:
        print(f"  [warn] extract_with_zipfile failed: {type(e).__name__}: {e}", file=sys.stderr)
        return None


def count_epub_chapters(epub_path: str) -> int:
    """Count spine items (approximate chapter count) without dependencies."""
    try:
        with zipfile.ZipFile(epub_path) as zf:
            opf_path = _find_opf_path(zf)
            if not opf_path:
                return 0
            opf_text = zf.read(opf_path).decode("utf-8", errors="replace")
            return len(re.findall(r'<itemref\b', opf_text))
    except Exception:
        return 0

