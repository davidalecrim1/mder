# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`mder` converts documents (PDF, EPUB, DOCX, HTML, Markdown, RTF, MOBI/AZW) into a **folder of structured markdown** for AI agents — one file per chapter plus `GLOSSARY.md`, `PATTERNS.md`, `CHEATSHEET.md`, and a `SKILL.md` index.

It is a fork of [book-to-skill](https://github.com/virgiliojr94/book-to-skill). The key divergence: upstream installs each converted book **as an agent skill** into a skills directory (`~/.claude/skills/`, etc.); this fork writes plain markdown folders to a chosen `--output` directory (default `~/.mder/`) that are **not** auto-discovered as skills. Preserve this distinction when editing — generated output must never be written into a skills root.

## Architecture

The pipeline has two halves that meet at a temp workdir. This split is the single most important thing to understand:

1. **Extractor (Python, deterministic)** — the `mder/` package, invoked via the `scripts/extract.py` shim. It only turns source documents into clean text + metadata:
   - Writes `full_text.txt` and `metadata.json` into `MDER_WORKDIR` (env var; default `<tempdir>/mder_work/`, defined in `mder/config.py`).
   - It does **not** decide the final output location and does **not** generate the markdown folder.
   - `mder/utils.py` holds the real logic: CLI parsing (`parse_arguments`), multi-source resolution (`resolve_input_files`, expands files/dirs/globs), chapter/ToC detection (`detect_structure`), token estimation, and the `main()` entrypoint. `mder/parsers/` has one module per format (best tool with stdlib fallback). `mder/sanitize.py` strips zero-width/Unicode-tag characters from extracted text.

2. **Generator (spec-driven, run by the host agent)** — `SKILL.md` at the repo root is the generator spec, not documentation. The agent follows its numbered Steps 0–9 to read `full_text.txt` and *write the output folder itself*. **The output directory lives in SKILL.md, not in Python.** Step 0 parses `--input`/`--output`/`--raw-only` (plus a legacy positional form); Step 5 sets the destination to `--output` (default `~/.mder/`) and writes `<output>/<slug>/`. `--raw-only` (Mode 4) writes only `chapters/raw/` + a lean `SKILL.md` index — no summaries, glossary, patterns, or cheatsheet. When changing where or how generated files are written, edit `SKILL.md` — not the extractor.

`tools/` are dev utilities: `validate_skill.py` (audits a generated SKILL.md against per-host rules via `--lens`), `discovery_tax.py` (token-cost model), `scan_generated_skill.py`.

## Commands

The `Makefile` mirrors the locally-reproducible CI jobs (test, lint, smoke,
security, validate-skill). Run `make ci` to reproduce them all, or an
individual target. `make install-dev` installs pytest, ruff, and bandit.

```bash
# Tests (433 currently pass)
python3 -m pytest -q
python3 -m pytest tests/test_mder.py -q                 # one file
python3 -m pytest tests/test_mder.py::TestCliHelp -q    # one class
python3 -m pytest -k "ergodic or tilde" -q              # by keyword

# Lint (matches CI: syntax + pyflakes only, style is ungated)
ruff check --select E9,F --target-version py310 mder/ scripts/ tests/ tools/

# Security (matches CI)
bandit -q -r mder scripts tools --severity-level high --confidence-level medium

# Run the extractor directly (produces text only, into MDER_WORKDIR)
python3 scripts/extract.py <path-or-glob> --mode text --install-missing no
python3 scripts/extract.py --check          # report which format extractors are installed
MDER_WORKDIR=/some/dir python3 scripts/extract.py book.epub --mode text
```

Console entry point is `mder = mder.cli:main` (which delegates to `mder.utils.main`).

## Conventions

- Docs pages under `docs/` use SHOUTING_CASE filenames (e.g. `HOW_IT_WORKS.md`), except `index.md` and `404.md` which MkDocs requires lowercase. `mkdocs.yml` nav, the `redirects` map, and cross-links must stay in sync when renaming a page.
- Supported host agents are Claude Code, Codex, and OpenCode. Skill roots probed for the helper script: `~/.claude/skills/` and the cross-agent `~/.agents/skills/` (plus project-local `.claude/`, `.agents/`).
- CI jobs call `make` targets (`make test`/`lint`/`smoke`/`security`/`validate-skill`) so local and CI run the exact same commands — change the command in the `Makefile`, not in `.github/workflows/ci.yml`. The `smoke` target generates its own `sample/note.md` before extracting it.
