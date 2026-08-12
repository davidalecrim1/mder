#!/usr/bin/env bash
#
# Install the mder skill into your coding agents.
#
#   curl -fsSL https://raw.githubusercontent.com/davidalecrim1/mder/master/install.sh | bash
#
# Claude Code reads ~/.claude/skills; Codex and OpenCode share ~/.agents/skills.
# The skill is cloned into both so /mder works in whichever agent you open.

set -euo pipefail

REPO="${MDER_REPO:-https://github.com/davidalecrim1/mder.git}"
TARGETS=(
  "$HOME/.claude/skills/mder"   # Claude Code
  "$HOME/.agents/skills/mder"   # Codex + OpenCode (cross-agent)
)

command -v git >/dev/null 2>&1 || { echo "error: git is required" >&2; exit 1; }

for dir in "${TARGETS[@]}"; do
  if [ -d "$dir/.git" ]; then
    echo "Updating $dir"
    git -C "$dir" pull --ff-only --quiet
  else
    echo "Installing $dir"
    rm -rf "$dir"
    mkdir -p "$(dirname "$dir")"
    git clone --depth 1 --quiet "$REPO" "$dir"
  fi
done

echo
echo "Done. Open Claude Code, Codex, or OpenCode and run:"
echo "  /mder --input ~/path/to/book.epub --output ~/Documents/mder/books/"
echo
echo "Check optional extractors (better EPUB/PDF/DOCX quality):"
echo "  python3 \"$HOME/.claude/skills/mder/scripts/extract.py\" --check"
