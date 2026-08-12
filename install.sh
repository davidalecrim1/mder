#!/usr/bin/env bash
#
# Install the mder skill into Claude Code, Codex, and OpenCode.
#
#   curl -fsSL https://raw.githubusercontent.com/davidalecrim1/mder/master/install.sh | bash
#
set -euo pipefail

REPO="${MDER_REPO:-https://github.com/davidalecrim1/mder.git}"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
git clone --depth 1 --quiet "$REPO" "$tmp"

# Claude Code reads ~/.claude/skills; Codex and OpenCode share ~/.agents/skills.
# Copy only the runnable skill (spec + extractor + package), not the whole repo.
for dir in "$HOME/.claude/skills/mder" "$HOME/.agents/skills/mder"; do
  mkdir -p "$dir"
  cp -R "$tmp"/SKILL.md "$tmp"/scripts "$tmp"/mder "$dir"/
  echo "installed -> $dir"
done

echo "Done. Run: /mder --input book.epub --output ~/Documents/mder/books/"
