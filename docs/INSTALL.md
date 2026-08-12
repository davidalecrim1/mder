---
description: "Install mder as an agent skill for Claude Code, Codex, and OpenCode, or as a standalone pip CLI. Every host path and optional extractor covered."
seo_title: "Install mder - Claude Code, Codex, OpenCode, or pip"
---

## Install

> **Two ways to use it, do not confuse them:**
> - **As an agent skill** (the `/mder` command in Claude Code, Codex, or OpenCode) → **`git clone` into your skills folder** (below). This is what gives you the slash command and the full convert-a-book flow.
> - **As a standalone CLI** (just the text extractor) → `pip install mder`, then `mder --help`. This does **not** register the agent skill; it only installs the extraction engine. See [the CLI section](#standalone-cli-pip).

The skill follows the open [Agent Skills](https://github.com/agentskills/agentskills) standard, so a single install works for any compatible host.

**One command, any host** — the [`skills` CLI](https://skills.sh) resolves the repo, detects the root `SKILL.md`, and installs the complete skill (including `scripts/extract.py` and `tools/`) into the skills folder of every host you select:

```bash
npx skills add davidalecrim1/mder
```

Prefer a manual install? Every per-host `git clone` path below works exactly the same.

**Codex / OpenCode** (cross-agent path both discover):

```bash
git clone https://github.com/davidalecrim1/mder.git ~/.agents/skills/mder
```

**Claude Code**:

Copy this into your Claude Code session:

```
Install mder: https://raw.githubusercontent.com/davidalecrim1/mder/master/SKILL.md
```

Or manually using standard `git clone` (ensures modular engine files are fetched correctly):

```bash
git clone https://github.com/davidalecrim1/mder.git ~/.claude/skills/mder
```

Then in any agent session:

```bash
/mder ~/path/to/your-book.pdf
# or
/mder ~/path/to/your-book.epub
```

### Standalone CLI (pip)

`pip install mder` is a **separate, optional** path. It installs only the
text-extraction engine as a CLI, for scripting or to grab the optional extractors;
it does **not** register the `/mder` agent skill (use the `git clone` above
for that).

```bash
pip install "mder[pdf,epub,docx]"   # engine + optional extractors
mder ~/path/to/book.pdf --mode text  # or: python -m mder ...
mder --check                          # report which extractors are installed
```

---


---

[ Back to the README](../README.md)
