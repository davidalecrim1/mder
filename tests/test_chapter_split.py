"""Tests for the deterministic chapter splitter (slugify, split_into_chapters).

The splitter slices extracted text into verbatim per-chapter raw files. It reuses
the same heading detector as detect_structure, drops table-of-contents stubs,
and collapses repeats of the same section (ToC entry + body + endnotes) while
keeping distinct numbering schemes (Roman parts vs Arabic chapters) separate.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from mder.utils import (  # noqa: E402
    slugify,
    split_into_chapters,
    write_chapter_files,
    sections_to_chapters,
    _section_title,
)


def _body(word, n=80):
    return (f"{word} body sentence. " * n) + "\n"


class TestSlugify:
    def test_accents_folded(self):
        assert slugify("Café — naïve résumé") == "cafe-naive-resume"

    def test_punctuation_and_case(self):
        assert slugify("Chapter 1. Why Turtles!") == "chapter-1-why-turtles"

    def test_cjk_yields_empty(self):
        # No ASCII form: caller falls back to the index for the filename.
        assert slugify("第一章 緒論") == ""

    def test_length_cap(self):
        s = slugify("word " * 40, max_len=20)
        assert len(s) <= 20 and not s.endswith("-")


class TestSplitIntoChapters:
    def test_front_matter_and_numbered_chapters(self):
        text = (
            "Title Page\n" + _body("front", 40) +
            "Chapter 1. Alpha\n" + _body("alpha") +
            "Chapter 2. Beta\n" + _body("beta")
        )
        chs = split_into_chapters(text)
        assert [c["index"] for c in chs] == ["ch00", "ch01", "ch02"]
        assert chs[0]["title"] == "Front Matter"
        assert chs[1]["number"] == 1 and chs[2]["number"] == 2
        # Raw text is a verbatim slice.
        assert "alpha body sentence." in chs[1]["text"]

    def test_toc_stubs_are_dropped(self):
        toc = "Contents\nChapter 1. Alpha\nChapter 2. Beta\n\n"
        text = (
            _body("front", 40) + toc +
            "Chapter 1. Alpha\n" + _body("alpha") +
            "Chapter 2. Beta\n" + _body("beta")
        )
        chs = split_into_chapters(text)
        numbers = [c["number"] for c in chs if c["number"]]
        # Only the two real chapters survive; ToC entries are stubs.
        assert numbers == [1, 2]

    def test_roman_parts_distinct_from_arabic_chapters(self):
        # "IV." (Roman 4) must not collapse into "Chapter 4".
        text = (
            "IV. Soul in the Game\n" + _body("part4") +
            "Chapter 4. The Skin of Others\n" + _body("chap4")
        )
        chs = split_into_chapters(text)
        titles = [c["title"] for c in chs]
        assert "IV. Soul in the Game" in titles
        assert "Chapter 4. The Skin of Others" in titles
        assert len(chs) == 2

    def test_body_wins_over_early_cross_reference(self):
        # A bare "Chapter 9" heading-like cross-reference appears before the body;
        # dedup keeps the long body and orders it by the body's position.
        text = (
            "Chapter 9\n" + _body("stub", 3) +   # short → dropped as a stub
            "Chapter 1. Start\n" + _body("one") +
            "Chapter 9. Real Body\n" + _body("nine", 120)
        )
        chs = split_into_chapters(text)
        nine = [c for c in chs if c["number"] == 9]
        assert len(nine) == 1
        assert "nine body sentence." in nine[0]["text"]

    def test_markdown_heading_fallback(self):
        text = (
            "# Intro\n" + _body("intro") +
            "# Methods\n" + _body("methods") +
            "# Results\n" + _body("results")
        )
        chs = split_into_chapters(text)
        titles = [c["title"] for c in chs]
        assert "Methods" in titles and "Results" in titles

    def test_write_chapter_files_pairs_index_and_slug(self, tmp_path):
        text = "Chapter 1. Alpha\n" + _body("alpha") + "Chapter 2. Beta\n" + _body("beta")
        chs = split_into_chapters(text)
        meta = write_chapter_files(chs, tmp_path / "chapters")
        files = sorted(p.name for p in (tmp_path / "chapters").glob("*.md"))
        assert files == ["ch00-chapter-1-alpha.md", "ch01-chapter-2-beta.md"]
        assert meta[0]["file"] == "chapters/ch00-chapter-1-alpha.md"
        assert (tmp_path / "chapters" / meta[0]["file"].split("/")[-1]).read_text(
            encoding="utf-8"
        ).startswith("Chapter 1. Alpha")

    def test_write_chapter_files_clears_stale(self, tmp_path):
        d = tmp_path / "chapters"
        d.mkdir()
        (d / "ch99-old.md").write_text("stale", encoding="utf-8")
        chs = split_into_chapters("Chapter 1. Alpha\n" + _body("alpha"))
        write_chapter_files(chs, d)
        assert not (d / "ch99-old.md").exists()


class TestSectionsToChapters:
    """The structural path used for EPUB spine/ToC sections — verbatim, no
    heading-guessing, so a chapter is never cut off at a false boundary."""

    def test_each_section_becomes_a_verbatim_chapter(self):
        secs = [
            "Chapter 1\nWhy Turtles\n" + _body("one"),
            "Chapter 2\nThe Minority\n" + _body("two"),
        ]
        chs = sections_to_chapters(secs)
        assert [c["index"] for c in chs] == ["ch00", "ch01"]
        # Verbatim: the whole section text is preserved, including a cross-
        # reference line that would fool heading detection.
        secs2 = ["Chapter 1\nBody. We will see further in\nChapter 19\nthat me is a group. THE END\n"]
        chs2 = sections_to_chapters(secs2)
        assert len(chs2) == 1
        assert "THE END" in chs2[0]["text"]  # not truncated at "Chapter 19"

    def test_slug_from_chapter_name(self):
        # A bare "Chapter 9" gains its subtitle so the slug is identifiable.
        secs = ["Chapter 9\nSurgeons Should Not Look Like Surgeons\n" + _body("nine")]
        chs = sections_to_chapters(secs)
        assert chs[0]["slug"].startswith("chapter-9-surgeons")

    def test_empty_sections_skipped(self):
        chs = sections_to_chapters(["", "   \n\n", "Real\n" + _body("real")])
        assert len(chs) == 1

    def test_section_title_plain_heading(self):
        assert _section_title("Introduction\n\nsome body text here") == "Introduction"
