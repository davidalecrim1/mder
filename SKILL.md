---
name: mder
description: "Converts books and documents (PDF, EPUB, DOCX, HTML, Markdown, plain text, RTF, MOBI/AZW with Calibre) into structured markdown knowledge folders for AI agents, extracting frameworks, mental models, principles, techniques, and anti-patterns. Use when the user wants to study a document through Claude Code, Codex, or OpenCode, apply an author's frameworks while working, or build a reusable knowledge base from a file."
---

<!--
Cross-agent notes (informational; ignored by host agents):
  - Compatible skill roots: Claude Code (~/.claude/skills, .claude/skills),
    Codex / OpenCode cross-agent (~/.agents/skills, .agents/skills).
  - `allowed-tools` is intentionally omitted to stay agent-neutral. The skill needs
    shell (to run extract.py) and file read/write — each host prompts for those on
    first use.
  - Argument hint: [--input <path>]... [--output <dir>] [--raw-only] <path-or-folder-or-glob>... [skill-name-slug]
-->

# mder - Document-to-Markdown

Transform written knowledge into structured markdown knowledge folders by extracting structure — not producing summaries.

## Philosophy

Books contain crystallized expertise: frameworks, principles, and techniques that took years to develop. This skill extracts that knowledge into a format Claude Code, Codex, OpenCode, or another compatible agent can leverage repeatedly.

Each chapter is kept in **two forms**: a distilled summary (`chapters/summary/`)
for fast reasoning, and the verbatim source text (`chapters/raw/`) for when the
full chapter is needed. An agent reads the summary first and opens the raw file
when precision matters — never a paraphrase standing in for the real text.

**Extract structure, not summaries.** A skill isn't a book report. It's a toolkit of:
- Named frameworks (mental models with clear application)
- Actionable principles (rules that guide decisions)
- Techniques (step-by-step methods)
- Anti-patterns (what to avoid and why)
- Voice calibration (how the author thinks and communicates)

**Preserve the author's precision.** Frameworks often have specific names for reasons. "The 5 Whys" isn't interchangeable with "ask why multiple times." Capture the exact formulation.

**Layer depth appropriately.** Simple books → simple skills. Complex books with 10+ frameworks → skills with reference files and on-demand chapters.

---

## Modes of Operation

Five paths available. Route based on what the user asks:

### 1. Full Conversion (Default)
**Trigger:** User provides one or more document/directory/glob paths without special instructions
**Action:** Run all steps below (Steps 0–9)
**Output:** Complete folder with SKILL.md, `chapters/summary/` (distilled) + `chapters/raw/` (verbatim), glossary, patterns, cheatsheet

### 2. Analyze Only
**Trigger:** User says "analyze", "just extract", or "I want to review before generating"
**Action:** Run Steps 0–3, then produce a structured extraction report (frameworks, principles, techniques found). Stop — do NOT generate skill files.
**Output:** Analysis report for user review

### 3. Generate from Prior Analysis
**Trigger:** User has existing analysis notes or previously ran analyze-only
**Action:** Skip Steps 0–3, use the provided analysis as input, run Steps 4–9
**Output:** Skill files from the provided analysis

### 4. Raw-Only Extraction
**Trigger:** The `--raw-only` flag is present (or the user says "raw only", "just split the chapters", "no summaries").
**Action:** Run Step 0, Step 1, Step 1.5, Step 2, Step 2.5, Step 5 (name/destination), and Step 6 (create dirs + copy raw chapters). Then **skip Steps 4, 7, and 8** and run the **Raw-Only variant of Step 9** (a lean SKILL.md index of the raw chapters — no summary column). Finish with Step 9.5 and Step 10.
**Output:** `<output>/<slug>/` with `chapters/raw/` and a `SKILL.md` index only — no `chapters/summary/`, no `GLOSSARY.md`, `PATTERNS.md`, or `CHEATSHEET.md`.

### 5. Update / Fold-in (Existing Skill)
**Trigger:** User provides one or more new source paths and indicates they want to update an existing skill (either by pointing to the existing skill folder, providing a skill slug that already exists in `SKILLS_HOME`, or explicitly requesting an update).
**Action:** Run Step 0 (out-of-scope check), Step 1 (validate inputs), Step 1.5 (identify book type), and Step 2 (extract new files). Then skip to Step 5 (identify/detect existing skill path) and run the **Update / Fold-in Workflow** to merge the new content into the existing skill files.
**Output:** Updated existing skill with new/revised chapter summaries and merged indexes/glossaries.

---

## Skill Locations

This converter can run from multiple skill systems. When looking for this converter's helper script (`scripts/extract.py`), prefer these locations in order:

1. Claude Code personal skills: `~/.claude/skills/`
2. Codex / OpenCode cross-agent personal skills: `~/.agents/skills/`
3. Project-local Claude skills: `.claude/skills/`
4. Project-local cross-agent skills: `.agents/skills/`

**Generated** knowledge folders do not go here — they are written to `--output` (default `~/.mder/`), never into a skill root (see Step 5).

---

## Step 0 — Out-of-scope check

If no arguments are provided, stop and respond:
> "mder requires a supported document path, folder, or glob pattern. Usage: `mder [--input <path>]... [--output <dir>] [--raw-only] <path-or-folder-or-glob>... [skill-name-slug]`"

Throughout the workflow, parse arguments as follows:
- **Flags (preferred):**
  - `--input <path>` — a source document/folder/glob. Repeatable; append each to `INPUT_PATHS`.
  - `--output <dir>` — the destination root under which the generated folder is written. Expand a leading `~`. Store as `OUTPUT_ROOT`.
  - `--raw-only` — a boolean switch (takes no value). Set `RAW_ONLY=true`. This selects **Mode 4 (Raw-Only Extraction)**: only the raw chapter split and a lean `SKILL.md` index are written — no summaries, glossary, patterns, or cheatsheet. Default is `RAW_ONLY=false`.
- **Positional (legacy, still supported):** any bare argument that is a file, folder, or glob → append to `INPUT_PATHS`. A trailing argument that is not an existing path but looks like a skill slug (lowercase hyphens, alphanumeric) → treat as `SKILL_NAME`.
- If `OUTPUT_ROOT` was not provided, default it to `$HOME/.mder`.
- If any input path is an existing skill directory (contains `SKILL.md` and a `chapters/` sub-folder), or if `SKILL_NAME` matches an existing skill slug in `SKILLS_HOME`, flag this run as an **Update/Fold-in** operation (Mode 4).

---

## Step 1 — Validate input

Verify that there is at least one supported file, directory, or glob pattern among the `INPUT_PATHS`.
For directories and globs, expand them to find matching supported files (`.pdf`, `.epub`, `.docx`, `.txt`, `.md`, `.markdown`, `.rst`, `.adoc`, `.html`, `.htm`, `.rtf`, `.mobi`, `.azw`, `.azw3`).

If no supported files are found, stop with a clear error message.

---

## Step 1.5 — Identify content type

Before extracting, ask the user:

> "What kind of content do these sources have? This helps me choose the best extraction method.
>
> 1. **Technical** — has code blocks, tables, formulas, diagrams (e.g. programming books, academic papers, architecture guides)
> 2. **Text-heavy** — mostly prose, few or no tables/code (e.g. management, productivity, narrative non-fiction)
> 3. **Not sure** — I'll use the fast method and warn you if quality seems limited"

Store the answer as `BOOK_TYPE`:
- Option 1 → `BOOK_TYPE=technical`
- Option 2 → `BOOK_TYPE=text`
- Option 3 → `BOOK_TYPE=text`

**If `BOOK_TYPE=technical`**, inform the user before proceeding:
> "📐 Technical mode selected — using Docling for structure-aware extraction (tables, code blocks, formulas preserved as markdown). This takes ~1.5s per page, so expect a few minutes for longer sources. Starting now…"

**If `BOOK_TYPE=text`**, inform:
> "📄 Text mode selected — using the fastest suitable extractor for each file type. Plain text/Markdown/HTML are usually ready in seconds; PDFs use pdftotext when available."

---

## Step 2 — Extract text from the source documents

Run the extraction script, passing the input paths:

```bash
SCRIPT_PATH=""
for candidate in \
  "$HOME/.claude/skills/mder/scripts/extract.py" \
  "$HOME/.agents/skills/mder/scripts/extract.py" \
  ".claude/skills/mder/scripts/extract.py" \
  ".agents/skills/mder/scripts/extract.py"
do
  if [ -f "$candidate" ]; then
    SCRIPT_PATH="$candidate"
    break
  fi
done

if [ -z "$SCRIPT_PATH" ]; then
  echo "Could not find scripts/extract.py for mder" >&2
  exit 1
fi

PYTHON_BIN="${PYTHON_BIN:-python3}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  PYTHON_BIN="python"
fi

"$PYTHON_BIN" "$SCRIPT_PATH" $INPUT_PATHS --mode <BOOK_TYPE> --install-missing ask
```

Before extraction, the script checks optional Python packages needed for the detected format. If a better extractor is missing, it prompts the user with the available fallback. Non-interactive sessions default to fallback unless install mode is explicitly `yes`.

**Tip — preflight the environment:** run `"$PYTHON_BIN" "$SCRIPT_PATH" --check` to print a per-format report of which extractors are installed and the exact command to install whatever is missing, without processing any file. Useful when a user reports a setup or quality problem.

This creates:
- `<tempdir>/mder_work/full_text.txt` — combined extracted text of all sources with clear visually demarcated boundaries.
- `<tempdir>/mder_work/metadata.json` — overall combined size, words, pages, token counts, a detailed list of processed `sources`, and a **`chapters`** array (the canonical, deterministic chapter split) plus `chapters_dir`.
- `<tempdir>/mder_work/chapters/<index>-<slug>.md` — one **verbatim raw** file per chapter, sliced deterministically by the extractor. These are the source of truth for chapter boundaries and become `chapters/raw/` in the output.

Read `<tempdir>/mder_work/metadata.json` to inspect the results. Treat its
`chapters` list (each entry: `index`, `number`, `title`, `slug`, `file`, `chars`,
`words`) as the authoritative chapter set — do **not** re-derive chapter
boundaries by hand. Every generated summary pairs 1:1 with a raw file by
`<index>-<slug>`.

---

## Step 2.5 — Pre-flight cost estimate

Read `<tempdir>/mder_work/metadata.json` and present the user with an estimate **before doing any generation**:

```
📖 Sources detected: <total_sources> source(s)
<list each source filename and format from the sources metadata list>
📄 Combined Pages/Sections: ~<N> | Words: ~<N> | Total tokens: ~<N>K

💰 Estimated token cost (Full Conversion / Update):
   Input  (reading + prompts): ~<N>K tokens
   Output (skill files generated/updated):  ~<N>K tokens
   Total:                           ~<N>K tokens

   Cost: multiply the token counts above by your model's current
   input/output per-1M-token rates (prices and model names change often —
   do not hardcode them; quote today's rate and label it as an estimate).

   ⏱  Estimated time: ~<N> minutes

📁 Files to be generated/updated:
   SKILL.md + chapters/summary/ (distilled) + chapters/raw/ (verbatim, copied) + glossary + patterns + cheatsheet

➡  Proceed with Full Conversion / Update? (or type "analyze only" to preview first)
```

**How to estimate:**
- Input tokens ≈ `estimated_tokens` from metadata × 1.3 (prompts overhead per chapter pass)
- Output tokens ≈ chapters × per-chapter budget + 4,000 (SKILL.md) + 4,500 (glossary + patterns + cheatsheet)
  - Per-chapter budget midpoint by `BOOK_TYPE` (DEPTH is decided later in Step 4 and can raise it): `text` ≈ 1,000, `technical` ≈ 1,800. If the user has already indicated reference-only vs deep study, use the matching row of the Step 7 matrix.
- Cost: report the token counts and multiply by the user's current per-1M-token input/output rates. Do NOT hardcode dollar figures — model names and prices change; if you show one, label it an estimate and date it.

Wait for the user to confirm before proceeding. If they say "analyze only", switch to Mode 2.

---

## Step 2.6 — REPL-style access for large books (> 50k tokens)

Inspired by the Recursive Language Model (RLM) paradigm: treat `full_text.txt` as a queryable corpus, not a single read. Loading the whole file into context burns budget you will need later for generation.

For books over ~50k tokens, prefer programmatic probes over `Read(full_text.txt)` without bounds:

```bash
# Size check before any Read
wc -w "$FULL_TEXT_PATH"

# Find chapter offsets without loading the whole file
grep -n -E "^\s*(Chapter|CHAPTER)\s+[0-9]+" "$FULL_TEXT_PATH" | head -40

# Pull only the chapter you need (lines start..end inclusive)
sed -n '<start>,<end>p' "$FULL_TEXT_PATH"

# Verify a framework is actually mentioned before claiming it in SKILL.md
grep -c -i "westrum\|dora" "$FULL_TEXT_PATH"

# Targeted Read with offset/limit avoids dumping the full file
# Read(file_path=full_text.txt, offset=<line>, limit=<lines>)
```

Use this approach for Step 3 (structure analysis), Step 7 (per-chapter summaries), and Step 8 (glossary / patterns extraction). On books under 50k tokens, a single `Read` is fine.

Why this matters: a 200-page book is ~75k tokens. Re-reading it once per chapter (28 passes) costs ~2M input tokens; using grep + sed to pull only relevant slices keeps generation cost proportional to the output, not the source.

---

## Step 3 — Analyze book structure

Read the first 8,000 characters of the extracted `full_text.txt` to identify:
- Book **title** and **author(s)**
- **Chapter structure** (look for "Chapter N", "PART I", numbered headings, table of contents)
- **Core themes** and subject domain
- Approximate number of chapters

Then read the Table of Contents section if present to map all chapters.

**If mode is "Analyze Only":** produce the extraction report now and stop. Structure:
```
## Extraction Report — <Title>

### Author's Core Frameworks
- **<Framework Name>**: <what it is and when to apply>

### Key Principles
- <Principle>: <actionable rule>

### Techniques & Methods
- <Technique>: <step-by-step or how-to>

### Anti-patterns
- <What to avoid>: <why>

### Suggested Skill Name
`{author-lastname}-{core-concept}` — e.g. `cialdini-influence`

### Chapters Detected
| # | Title | Main Frameworks |

(Use `metadata.chapters` as the authoritative chapter list — index, title, and
slug are already assigned. This section just annotates each with its frameworks.)
```

---

## Step 4 — Ask purpose (Full Conversion only)

**Skip this step entirely if `RAW_ONLY=true`** — no summaries are generated, so purpose/depth do not apply.

Before generating, ask the user:

> "What should this skill help you do? (Pick one or more)
> 1. Apply the author's frameworks while working
> 2. Think with the author's mental models
> 3. Reference specific chapters and concepts
> 4. All of the above"

Use the answer to weight what gets highlighted in the SKILL.md Core section.

**Derive `DEPTH` from the answer (no extra prompt):**
- Answer is **only** option 3 (reference) → `DEPTH=reference` — lean, fast-lookup chapters.
- Answer includes option 1, 2, or 4 → `DEPTH=study` — deeper chapters with more worked detail, examples, and reasoning.

`DEPTH` and `BOOK_TYPE` together set the per-chapter token budget in Step 7. Do **not** ask a separate "study vs reference" question — it is inferred here. (In Modes 2/3, where Step 4 is skipped, default `DEPTH=study`.)

---

## Step 5 — Determine skill name and destination

If `SKILL_NAME` was provided, use it as the slug.
Otherwise, derive the slug:
- **Single source:** slugify the input filename stem (lowercase, hyphens; e.g. `Skin in the Game by Nassim Nicholas Taleb.epub` → `skin-in-the-game-by-nassim-nicholas-taleb`). If the book has a strong methodological identity, you may instead propose the author-concept form (`{author-lastname}-{core-concept}`, e.g. `cialdini-influence`) and let the user choose.
- **Multiple sources:** propose an author-concept or title-based slug and let the user choose.

**Destination.** Set `SKILLS_HOME="$OUTPUT_ROOT"` — the `--output` value if given, otherwise the `$HOME/.mder` default. `mkdir -p "$SKILLS_HOME"` if it does not exist. Do **not** probe skill roots, run host detection, or write into `~/.claude/skills` — generated folders are plain markdown knowledge folders, not auto-installed skills. The user installs one as a skill later only if they choose to.

Check if `$SKILLS_HOME/<skill_name>/` already exists.
If it does, prompt the user to choose:
1. **Update / Fold-in** (Mode 4) — integrate new files/content into the existing skill components.
2. **Overwrite** — delete and regenerate the skill from scratch.
3. **Rename** — append `-2` or use a different custom slug.

If the user selects **Update / Fold-in**, proceed immediately to the **Update / Fold-in Workflow** section after Step 2.5 (skipping Steps 3, 4, 6, 7, 8, 9).

---

## Step 6 — Create directory structure and copy raw chapters

Chapters live in two parallel sub-folders: `summary/` (the distilled files you
write) and `raw/` (the verbatim source slices the extractor already produced).

If `RAW_ONLY=true`, create and copy **only** `chapters/raw/` — skip the
`chapters/summary/` directory entirely (no summaries will be written).

```bash
# Full Conversion only: clear any prior chapters so a regeneration with a
# different chapter count or slugs can't leave stale files behind. (Do NOT run
# this on an Update/Fold-in — that path merges into the existing folder.)
rm -rf "$SKILLS_HOME/<skill_name>/chapters/summary" "$SKILLS_HOME/<skill_name>/chapters/raw"
mkdir -p "$SKILLS_HOME/<skill_name>/chapters/raw"
# Skip the next line when RAW_ONLY=true:
mkdir -p "$SKILLS_HOME/<skill_name>/chapters/summary"

# Copy the deterministic raw chapter files from the workdir (path is
# metadata.chapters_dir). This is a plain file copy — it costs zero tokens and
# keeps the chapter text verbatim; never re-emit raw content by hand.
cp -R "$CHAPTERS_DIR"/. "$SKILLS_HOME/<skill_name>/chapters/raw/"
```

On a re-run over an existing folder, also overwrite the top-level `SKILL.md`,
`GLOSSARY.md`, `PATTERNS.md`, and `CHEATSHEET.md` (they are single files, so a
rewrite replaces them cleanly).

`$CHAPTERS_DIR` is `metadata.chapters_dir` (e.g. `<tempdir>/mder_work/chapters`).
After this, `chapters/raw/` holds one `<index>-<slug>.md` per entry in
`metadata.chapters`.

---

## Step 7 — Generate chapter summaries

**If `RAW_ONLY=true`, skip this entire step and Step 8, and go straight to the
Raw-Only variant of Step 9.** No summaries, glossary, patterns, or cheatsheet
are produced in raw-only mode.

**TOKEN BUDGET RULE — CRITICAL (adaptive):**

The per-chapter budget scales with `BOOK_TYPE` and `DEPTH`. Technical chapters need room for code and tables; study depth needs room for worked reasoning. Pick the budget from this matrix:

| | `DEPTH=reference` | `DEPTH=study` |
|---|---|---|
| `BOOK_TYPE=text` | 800–1,200 tokens | 1,000–1,800 tokens |
| `BOOK_TYPE=technical` | 1,200–1,800 tokens | 2,000–3,000 tokens |

- These are per-file targets, not hard caps — a dense chapter may run over, a thin one under. Density still beats length (Quality Rule #3): never pad to hit a number.
- Files are loaded on-demand, so a larger chapter only costs tokens when that chapter is actually read.
- When in doubt between two cells (e.g. mixed-content book), use the lower budget and let depth come from precision, not volume.

**`DEPTH=study` is earned with content, not a bigger number.** The standard section template (Core Idea → Connects To) naturally lands a dense prose chapter around 700–900 tokens. To reach the study budget *honestly* — not by padding — a study-depth chapter must add concrete material:
- **Reproduce one worked example or artifact** from the chapter (e.g. the example press release, a sample dialogue, a filled-in template, a decision the author walks through) under a `## Worked Example` section. This is the single biggest lever and the main thing a learner returns for.
- **Expand the "How" of each framework** into explicit steps or criteria, not a one-liner.
- **Add a short "Why it works / failure mode" note** to the top 1–2 frameworks.

If a chapter genuinely has no worked example and resists expansion, let it land below the study floor rather than padding — and note that the chapter is thin in its Core Idea. A `reference`-depth chapter, by contrast, deliberately omits worked examples and keeps only the decision-ready essentials.

For EACH entry in `metadata.chapters` (the canonical chapter list):

Read its raw file at `$SKILLS_HOME/<skill_name>/chapters/raw/<index>-<slug>.md`
(already copied in Step 6) — that is the exact chapter text. Do not re-slice
`full_text.txt` by hand.

Create the summary at `$SKILLS_HOME/<skill_name>/chapters/summary/<index>-<slug>.md`
— **the same `<index>-<slug>` filename as the raw file**, so summary and raw pair
1:1. Use the structure below. At the top of each summary, link to its verbatim
source: `> Full text: [raw](../raw/<index>-<slug>.md)`.

**Adapt emphasis based on `BOOK_TYPE`:**
- `technical` → prioritize "Code Examples", "Reference Tables", and "Commands & APIs" sections; preserve exact syntax
- `text` → prioritize "Frameworks Introduced", "Mental Models", and "Key Takeaways"; skip empty technical sections

```markdown
# Chapter N: <Full Title>

## Core Idea
<1–2 sentences: the single most important thing this chapter teaches>

## Frameworks Introduced
- **<Framework Name>**: <exact formulation — preserve the author's naming>
  - When to use: <specific situation>
  - How: <steps or criteria>

## Key Concepts
- **<Term>**: <precise definition in 1 sentence>
(5–10 most important terms from this chapter)

## Mental Models
<2–4 frameworks or thinking tools. Write as "Use X when Y" or "Think of X as Y">

## Anti-patterns
- **<What to avoid>**: <why it fails>

## Code Examples *(technical books only — omit if BOOK_TYPE=text)*
<!-- Copy the most instructive snippet from the chapter. Preserve indentation exactly. -->
```<language>
<key code example from this chapter>
```
- **What it demonstrates**: <one line>

## Reference Tables *(technical books only — omit if BOOK_TYPE=text)*
<!-- Reproduce any comparison matrix, parameter table, or decision table from the chapter in markdown. -->

## Worked Example *(DEPTH=study only — omit for DEPTH=reference)*
<!-- Reproduce or reconstruct one concrete example the author works through: a
     sample document, a dialogue, a filled-in template, a before/after, or a
     decision walked end-to-end. This is what makes a study chapter worth its
     budget. Keep it faithful to the source; never copy long raw passages —
     reconstruct the example compactly. -->

## Key Takeaways
1. <Actionable insight>
2. <Actionable insight>
3. <Actionable insight>
(3–7 takeaways a practitioner must remember)

## Connects To
- **Ch N**: <why this chapter relates>
- **<Concept>**: <external concept or standard it connects with>
```

---

## Step 8 — Generate supporting files

**Skip this entire step if `RAW_ONLY=true`** — GLOSSARY/PATTERNS/CHEATSHEET are not produced in raw-only mode.

**Chapter references — always link to the summary.** Whenever one of these files
cites a chapter, make it a markdown link to that chapter's **summary** file
(`chapters/summary/<index>-<slug>.md`), never the raw file and never a bare
`(Ch N)`. The summary is the right entry point: it already links to the verbatim
raw chapter at its top (`> Full text: [raw](../raw/<index>-<slug>.md)`), so a
reader who needs the exact source is one hop away. Reference chain:
supporting file → chapter summary → raw text.

### GLOSSARY.md
Create `$SKILLS_HOME/<skill_name>/GLOSSARY.md`:
- Every significant term from the book, alphabetically sorted
- Format: `**Term** — definition ([ch<N>](chapters/summary/ch<N>-<slug>.md))`
  (link to the summary; multiple chapters → one link each)
- Max 1,500 tokens

### PATTERNS.md
Create `$SKILLS_HOME/<skill_name>/PATTERNS.md`:
- All concrete techniques, design patterns, algorithms from the book
- Format: `## Pattern Name\n**When to use**: ...\n**How**: ...\n**Trade-offs**: ...\n**Source**: [ch<N>](chapters/summary/ch<N>-<slug>.md)`
- Max 2,000 tokens

### CHEATSHEET.md
Create `$SKILLS_HOME/<skill_name>/CHEATSHEET.md`:

**This is the most differentiated layer of the skill — treat it as a reasoning aid, not a keyword list.** Anyone can grep the glossary for a term. The cheatsheet captures the author's *judgment*: the decisions they'd make and why. It's the file that turns "I know the words" into "I'd act the way the author would".

Prioritize, in order:
1. **Decision rules** — "When X, do Y, because Z." The if/then logic the author applies, stated so the reader can apply it without re-reading the book.
2. **Decision trees / flowcharts** (as nested bullets or a small table) — for choices with more than two branches.
3. **Trade-off matrices** — competing options scored on the dimensions the author cares about, so the reader can pick under their own constraints.
4. **Thresholds & defaults** — the specific numbers, ratios, or rules of thumb the author commits to (e.g. "keep functions under ~20 lines", "alert when error budget < 10%").
5. **Tells & smells** — fast heuristics for recognizing a situation ("if you see X, you're probably in trouble Y").

Avoid: bare term→definition rows (that's the glossary), and prose paragraphs (that's the chapters). Every line should help the reader *decide* something.

- Format mostly as compact tables and decision rules; the content you'd want on a single printed page kept beside you while working.
- When a rule traces to a specific chapter, link it to that chapter's summary (`[ch<N>](chapters/summary/ch<N>-<slug>.md)`).
- Max 1,200 tokens.

---

## Step 9 — Generate the master SKILL.md

**CRITICAL TOKEN BUDGET: Keep SKILL.md body under 4,000 tokens.**
Compaction truncates from the END — put the most important content FIRST.

Create `$SKILLS_HOME/<skill_name>/SKILL.md`:

```markdown
---
name: <skill_name>
description: "Knowledge base from \"<Full Title>\" by <Author(s)>. Use when applying <author>'s frameworks for <key topics, 3–6 terms>, studying the book, or referencing its concepts."
---

<!-- argument-hint: [topic, framework name, or chapter number] -->

# <Full Title>
**Author**: <Author(s)> | **Pages**: ~<N> | **Chapters**: <N> | **Generated**: <YYYY-MM-DD>

## How to Use This Skill

- **Without arguments** — load core frameworks for reference
- **With a topic** — ask about `replication`, `pricing`, or another indexed topic; I find and read the relevant chapter
- **With chapter** — ask for `ch05`; I load that specific chapter
- **Browse** — ask "what chapters do you have?" to see the full index

When you ask about a topic not covered in Core Frameworks below, I will read
the relevant chapter file before answering.

---

## Core Frameworks & Mental Models
<!-- ~2,000 tokens: the author's most important named frameworks and principles.
     Preserve exact names. Write as "Use X when Y", "Prefer X over Y because Z".
     This is a toolkit, not a summary. -->

<generate 2,000 tokens of the most critical frameworks and insights here>

---

## Chapter Index

Each chapter has a distilled summary and the full verbatim text (same filename
under `chapters/raw/`).

| # | Title | Summary | Raw | Key Frameworks |
|---|-------|---------|-----|----------------|
| ch01 | <Title> | [summary](chapters/summary/ch01-<slug>.md) | [raw](chapters/raw/ch01-<slug>.md) | <framework1>, <framework2> |
| ch02 | <Title> | [summary](chapters/summary/ch02-<slug>.md) | [raw](chapters/raw/ch02-<slug>.md) | <framework1>, <framework2> |
...

## Topic Index

<!-- Alphabetical. Major terms/frameworks → chapter(s) that cover them. -->
- **<Term>** → ch<N>[, ch<N>]
- **<Term>** → ch<N>

## Supporting Files

- [GLOSSARY.md](GLOSSARY.md) — all key terms with definitions
- [PATTERNS.md](PATTERNS.md) — all techniques and design patterns
- [CHEATSHEET.md](CHEATSHEET.md) — quick reference tables and decision guides

---

## Scope & Limits

This skill covers the book content only. For hands-on implementation in your codebase,
combine with project-specific tools. For topics beyond this book, check related skills
or ask the agent directly.
```

---

### Step 9 — Raw-Only variant (when `RAW_ONLY=true`)

Write a lean `$SKILLS_HOME/<skill_name>/SKILL.md` that indexes the raw chapters
only. There is **no** Core Frameworks section, **no** summary column, and **no**
Supporting Files section (those files were not generated). Keep the body under
4,000 tokens.

```markdown
---
name: <skill_name>
description: "Raw chapter extract of \"<Full Title>\" by <Author(s)>. Verbatim source text split by chapter, with no summaries. Use to read or search the original text of <key topics, 3–6 terms>."
---

<!-- argument-hint: [chapter number or topic] -->

# <Full Title>
**Author**: <Author(s)> | **Pages**: ~<N> | **Chapters**: <N> | **Generated**: <YYYY-MM-DD>
**Mode**: raw-only (verbatim chapter text; no summaries or reference files)

## How to Use This Skill

- **With a chapter** — ask for `ch05`; I open that raw chapter file.
- **With a topic** — ask about a term; I grep the raw chapters and read the matches.
- **Browse** — ask "what chapters do you have?" to see the full index.

There are no distilled summaries in this skill — every answer is read directly
from the verbatim chapter text under `chapters/raw/`.

## Chapter Index

| # | Title | Raw |
|---|-------|-----|
| ch01 | <Title> | [raw](chapters/raw/ch01-<slug>.md) |
| ch02 | <Title> | [raw](chapters/raw/ch02-<slug>.md) |
...

---

## Scope & Limits

This skill contains the verbatim source text only, split by chapter — no
summaries, glossary, patterns, or cheatsheet. Regenerate without `--raw-only`
to produce the full distilled knowledge folder.
```

Then continue to Step 9.5 and Step 10.

## Step 9.5 — Scan the generated skill

Before reporting success, loading the skill in another session, or publishing it, run the advisory security scan:

```bash
SKILL_CONVERTER_ROOT="$(cd "$(dirname "$SCRIPT_PATH")/.." && pwd)"
"$PYTHON_BIN" "$SKILL_CONVERTER_ROOT/tools/scan_generated_skill.py" "$SKILLS_HOME/<skill_name>"
```

If the scanner exits non-zero, stop and ask a human to review its file/line findings. Do not silently rewrite the generated files, and do not load or publish the skill until the findings are resolved or explicitly accepted.

---

## Step 10 — Cleanup and report

```bash
PYTHON_BIN="${PYTHON_BIN:-python3}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  PYTHON_BIN="python"
fi

"$PYTHON_BIN" - <<'PY'
import os
import shutil
import tempfile
from pathlib import Path
shutil.rmtree(
    os.environ.get("MDER_WORKDIR", Path(tempfile.gettempdir()) / "mder_work"),
    ignore_errors=True,
)
PY
```

Then report to the user:

```
✅ Skill created: $SKILLS_HOME/<skill_name>/

📚 Book: <Full Title> — <Author>
📄 Pages: ~<N> | Chapters: <N>

Files generated:
  SKILL.md            — core frameworks + index   (~X tokens)
  chapters/summary/   — <N> distilled chapters    (~X tokens each, ~X total)
  chapters/raw/       — <N> verbatim chapters      (full source text)
  GLOSSARY.md         — key terms                 (~X tokens)
  PATTERNS.md         — techniques & patterns     (~X tokens)
  CHEATSHEET.md       — quick reference           (~X tokens)
  ─────────────────────────────────────────────────────
  Total skill size: ~X tokens (loaded on-demand, not all at once)

💡 Tip: check your agent's session cost/usage command to see actual token usage.

Usage:
  Ask for <skill_name>                  → load core frameworks
  Ask <skill_name> about <topic>        → find and explain a topic
  Ask <skill_name> for ch<N>            → dive into a specific chapter

Reload (if your agent doesn't auto-detect new skills):
  Claude Code:        restart the session
  Codex / OpenCode:   reload skills or restart the session
```

**Raw-only report:** when `RAW_ONLY=true`, drop the `chapters/summary/`,
`GLOSSARY.md`, `PATTERNS.md`, and `CHEATSHEET.md` lines from the "Files
generated" list (only `SKILL.md` and `chapters/raw/` were written), and note
that the folder can be regenerated without `--raw-only` for the full distilled
version.

---

## Update / Fold-in Workflow

When performing an Update/Fold-in operation on an existing skill at `$SKILLS_HOME/<skill_name>/`:

### 1. Read Existing Skill Structure
Read and parse the existing skill's files:
- Read `$SKILLS_HOME/<skill_name>/SKILL.md` to parse the existing **Chapter Index**, **Topic Index**, metadata (author, total chapters), and **Core Frameworks**.
- List `$SKILLS_HOME/<skill_name>/chapters/summary/` to find the highest chapter index (e.g. `ch12`). (Older skills may have a flat `chapters/`; if so, migrate those files into `chapters/summary/` and create `chapters/raw/`.)
- Read `$SKILLS_HOME/<skill_name>/GLOSSARY.md`, `$SKILLS_HOME/<skill_name>/PATTERNS.md`, and `$SKILLS_HOME/<skill_name>/CHEATSHEET.md` to see what terms and frameworks are already indexed.

### 2. Match Content & Identify Revisions vs. Additions
The new extraction produced its own `metadata.chapters` list and raw files. Identify whether each new chapter is:
- **An update/revision to an existing chapter**: merge the new details into the existing `chapters/summary/<index>-<slug>.md` and refresh its `chapters/raw/` counterpart from the new raw file.
- **A new addition**: append it, continuing the index after the highest existing one (e.g. existing stops at `ch12` → new files become `ch13-*`, `ch14-*`). Keep the summary and raw filenames identical.

### 3. Generate or Update Chapter Files
For each new or revised chapter:
- Copy its raw file into `$SKILLS_HOME/<skill_name>/chapters/raw/<index>-<slug>.md` (from `metadata.chapters_dir`; re-index the filename if it collides with an existing chapter).
- Read that raw file and follow **Step 7** to write/update the summary at `$SKILLS_HOME/<skill_name>/chapters/summary/<index>-<slug>.md` (same filename).

### 4. Merge Supporting Files
- **Merge GLOSSARY.md**:
  - Read the existing `$SKILLS_HOME/<skill_name>/GLOSSARY.md`.
  - Extract all new terms and definitions from the new content (Step 8 glossary guidelines).
  - Combine and alphabetize the list of existing and new terms.
  - If a term already exists, append the new chapter references to it as summary links (e.g. `**Term** — definition ([ch04](chapters/summary/ch04-<slug>.md), [ch13](chapters/summary/ch13-<slug>.md))`).
  - Rewrite `$SKILLS_HOME/<skill_name>/GLOSSARY.md` with the fully merged, alphabetized list.
- **Merge PATTERNS.md**:
  - Read existing `$SKILLS_HOME/<skill_name>/PATTERNS.md`.
  - Extract any new techniques, algorithms, or patterns from the new content.
  - Append the new patterns, ensuring consistent formatting, and keeping the total length concise (under 2,500 tokens).
- **Merge CHEATSHEET.md**:
  - Read existing `$SKILLS_HOME/<skill_name>/CHEATSHEET.md`.
  - Extract new comparison rules, decision tables, or parameter guides.
  - Integrate them cleanly into the cheatsheet structure.

### 5. Re-generate the Master SKILL.md
Update the master skill file `$SKILLS_HOME/<skill_name>/SKILL.md`:
- **Metadata**: Increment the chapter count, update the estimated page count, and add the new source names if appropriate. Update the `Generated` date to the current date.
- **Core Frameworks**: Fold in the most high-impact mental models or principles from the new content (ensuring the overall file remains under 4,000 tokens).
- **Chapter Index**: Append the new chapters to the index table, with both the `chapters/summary/<index>-<slug>.md` and `chapters/raw/<index>-<slug>.md` links (matching the Step 9 table format).
- **Topic Index**: Merge the new topics alphabetically. If an existing topic is also covered in the new chapters, append the new chapter links to its line (e.g. `- **Topic** → ch05, ch13`).

### 6. Scan, Cleanup, and Report
Once the files are successfully written and merged, run **Step 9.5**, then proceed to **Step 10** to perform cleanup and print a custom update report summarizing the newly added chapters, merged glossary terms, and updated indices.

---

## Quality Rules

1. **Extract structure, not summaries** — capture named frameworks, exact formulations, anti-patterns; not chapter recaps
2. **Preserve the author's precision** — "The 5 Whys" ≠ "ask why multiple times"; keep exact naming
3. **Density over completeness** — a 1,000-token summary beats a 10,000-token excerpt
4. **Practitioner voice** — write "Use X when Y", not "The book explains X"
5. **Front-load SKILL.md** — compaction keeps the first 5,000 tokens; most important content comes first
6. **Chapter files are on-demand** — they don't count against skill budget until loaded
7. **Never copy raw book text** — always synthesize, summarize, extract signal
8. **Topic index is critical** — it's how the agent navigates to the right chapter file
