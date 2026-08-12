# mder

Point `mder` at a book, folder, or glob and it turns the source into a structured **markdown folder** — one file per chapter, plus a glossary, patterns, and a cheatsheet — that an AI agent loads on demand while you work.

Handles PDF, EPUB, DOCX, Markdown, plain text, reStructuredText, AsciiDoc, HTML, RTF, and MOBI/AZW (via Calibre).

`mder` is based on [book-to-skill](https://github.com/virgiliojr94/book-to-skill/tree/master), adapted so the output is not an installed agent skill but a plain folder of documents you keep wherever you want and reference by hand.

## Why

The usual way to give an agent a document is to chunk it and stuff it in a vector store. RAG retrieval returns fragments torn out of context — half a chapter, a stray paragraph, the wrong section — and the agent stitches them into answers that sound right and aren't. More retrieval, more hallucination, less of the document actually used well.

`mder` takes the opposite approach: preserve the document's own structure. One chapter becomes one file. When the agent needs chapter 1, it loads the *whole* chapter file into context — complete, in order, with its argument intact — instead of a handful of similarity-matched shards. The book's table of contents becomes a real index the agent can navigate, so retrieval is "open the right file," not "hope the embeddings matched."

The result: convert a book **once**, then ask your agent about it and get answers grounded in the real, contiguous text — no re-reading the whole PDF every turn, no chunk-salad hallucinations.

## Philosophy

Ingesting a book should mirror the book. `mder` maps the source's own shape onto the filesystem: each chapter becomes its own `.md` file, and the recurring, reusable knowledge is lifted into companion files — a glossary of the author's terms, a `patterns` file of frameworks and heuristics, a `cheatsheet` of decision rules. Nothing is flattened into one blob or shredded into context-free chunks.

That structure is what makes the result good to *work with*, not just store. An agent can open exactly the chapter a question is about, cross-reference the glossary, and pull a decision rule from the cheatsheet — then you keep asking and iterating against contiguous, faithful text instead of similarity-matched fragments. The document stops being a static PDF and becomes a knowledge base an agent can reason over chapter by chapter.

## How it works

Two halves:

1. A deterministic Python **extractor** turns the document into clean text + metadata, and slices it into one verbatim file per chapter (`scripts/extract.py`).
2. A spec-driven **generator** — your agent follows `SKILL.md` — distills each chapter and assembles the folder. Files are loaded on demand, so the core stays small.

Each converted book becomes a folder:

| File | Purpose |
|------|---------|
| `SKILL.md` | Core mental models + chapter index |
| `chapters/summary/ch01-*.md` … | Distilled chapter — one per chapter, loaded on demand |
| `chapters/raw/ch01-*.md` … | Verbatim source text for the same chapter (open when full detail is needed) |
| `glossary.md` | Key terms, alphabetically, with chapter refs |
| `patterns.md` | Techniques, algorithms, design patterns |
| `cheatsheet.md` | Decision tables and quick-reference rules |

Each `summary/` file pairs 1:1 with a `raw/` file by filename: reason over the summary, open the raw chapter when precision matters.

## Usage

```bash
/mder --input ~/path/to/book.epub --output ~/Documents/mder/books/
```

- `--input <path>` — a document, folder, or glob (repeatable).
- `--output <dir>` — destination root. Defaults to `~/.mder/`.

The result is written to `<output>/<book-slug>/` (e.g. `~/.mder/skin-in-the-game/`). The legacy positional form `/mder book.epub my-slug` still works.

## This fork

This is a personal fork of [virgiliojr94/book-to-skill](https://github.com/virgiliojr94/book-to-skill/tree/master).

The upstream project installs each converted book **as an agent skill** into your skills directory (`~/.claude/skills/`, etc.), where the host auto-discovers it. This fork changes that: converted books are written as plain **markdown folders** to a directory of your choice (default `~/.mder/`), so they are **not** preinstalled or auto-loaded. You load a file manually when you need it — and can still copy one into a skills directory later if you want it as a skill.

## License

MIT — applies to the converter (code + skill definition) in this repository, **not** to any book or document you process with it.
