---
description: "Turn any book, PDF or EPUB into a structured agent skill for Claude Code, Codex, and OpenCode. Named frameworks and decision rules, loaded on demand."
seo_title: "mder - Turn Any Book Into an AI Agent Skill"
hide:
  - navigation
  - toc
---

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "mder",
  "applicationCategory": "DeveloperApplication",
  "operatingSystem": "Linux, macOS, Windows",
  "description": "Converts books and documents (PDF, EPUB, DOCX, HTML, Markdown, RTF, MOBI/AZW) into structured, on-demand agent skills for Claude Code, Codex, and OpenCode.",
  "url": "https://davidalecrim1.github.io/mder/",
  "codeRepository": "https://github.com/davidalecrim1/mder",
  "license": "https://opensource.org/licenses/MIT",
  "offers": { "@type": "Offer", "price": "0", "priceCurrency": "USD" },
  "author": { "@type": "Person", "name": "davidalecrim1", "url": "https://github.com/davidalecrim1" }
}
</script>

# mder

<p style="font-size: 1.25rem; max-width: 42rem;">
Turn any book or document into a structured, on-demand agent skill — named frameworks, decision rules, and anti-patterns. <strong>Structure, not a summary.</strong>
</p>

[Get started](guide.md){ .md-button .md-button--primary }
[Skill reference](skill-reference.md){ .md-button }
[GitHub](https://github.com/davidalecrim1/mder){ .md-button }

---

## Why mder

<div class="grid cards" markdown>

-   :material-file-document-multiple:{ .lg .middle } __Multi-format__

    ---

    PDF, EPUB, DOCX, HTML, Markdown, RTF, MOBI/AZW (via Calibre). Extraction runs
    locally with graceful stdlib fallbacks — no upload, no lock-in.

-   :material-brain:{ .lg .middle } __Structure, not summaries__

    ---

    Named frameworks, mental models, decision rules, and anti-patterns — the
    author's toolkit, captured with their exact terms, not a book report.

-   :material-flash:{ .lg .middle } __On-demand chapters__

    ---

    Per-chapter files load only when the topic is relevant, so a 200-page book
    costs tokens proportional to the question, not the page count.

-   :material-robot-happy:{ .lg .middle } __Multi-agent__

    ---

    One `SKILL.md` runs on Claude Code, Codex, and OpenCode through the
    open Agent Skills standard.

</div>

## Install

**As an agent skill** (gives you the `/mder` command in Claude Code, Codex, OpenCode):

```bash
npx skills add davidalecrim1/mder
# or manually:
git clone https://github.com/davidalecrim1/mder.git ~/.claude/skills/mder
# then, in your agent session:
/mder /path/to/book.pdf [skill-name]
```

**As a standalone CLI** (just the text extractor, optional):

```bash
pip install "mder[pdf,epub,docx]"
mder /path/to/book.pdf --mode text
```

## Learn more

<div class="grid cards" markdown>

-   :material-sitemap:{ .lg .middle } __[Architecture](ARCHITECTURE.md)__

    ---

    How the deterministic extractor and the spec-driven generator fit together.

-   :material-speedometer:{ .lg .middle } __[Performance](PERFORMANCE.md)__

    ---

    The measured Discovery Loop Tax and real per-conversion token cost.

-   :material-book-open-page-variant:{ .lg .middle } __[Skill Reference](skill-reference.md)__

    ---

    The full `SKILL.md` spec: every step, depth budget, and quality rule.

</div>
