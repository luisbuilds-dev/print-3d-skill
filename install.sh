#!/usr/bin/env sh
# Installs the print-3d skill for Claude Code (your profile in ~/.claude/print-3d/ is never touched).
set -e
DEST="$HOME/.claude/skills/print-3d"
mkdir -p "$HOME/.claude/skills"
rm -rf "$DEST"
cp -R "$(dirname "$0")/print-3d" "$DEST"
echo "Installed in $DEST"
command -v uv >/dev/null 2>&1 || echo "Next: install uv -> curl -LsSf https://astral.sh/uv/install.sh | sh"
echo "Open Claude Code and say: set up my 3D printer"
