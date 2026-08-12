---
description: "Every way to run /mder: a single file, a folder, a glob, or a list of paths, with extraction modes, skill naming, and worked command examples."
seo_title: "Usage - Convert a Book, Folder, or Glob into an Agent Skill"
---

## Usage

```
/mder <path-to-document-folder-or-glob>... [skill-name-slug]
```

Supported document formats: PDF, EPUB, DOCX, TXT, Markdown, reStructuredText, AsciiDoc, HTML, RTF, MOBI/AZW/AZW3.

**Examples:**

```bash
# Process several files together into a unified skill
/mder ~/papers/paper1.pdf ~/notes/export.txt unified-research

# Process all supported files in a folder together
/mder ~/workspace/project-docs/ project-knowledge

# Process files matching a glob pattern
/mder "~/books/*.epub" my-library

# Update/fold new material into an existing skill folder
/mder ~/articles/new-paper.pdf ~/.claude/skills/project-knowledge
```

After the skill is created, use it like any other agent skill:

```bash
/designing-data-intensive-apps                  # load core mental models
/designing-data-intensive-apps replication      # find and explain a topic
/designing-data-intensive-apps ch05             # dive into chapter 5
/designing-data-intensive-apps "what chapters do you have?"
```

Claude Code, Codex, and OpenCode pick up the new folder on the next session; reload skills if your agent doesn't auto-detect it.

---


---

[ Back to the README](../README.md)
