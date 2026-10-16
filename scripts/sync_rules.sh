#!/bin/sh
# AGENTS.md is the single source of truth for agent rules.
# Other tools look for their own filenames, so copy it to each one.
set -eu
cd "$(dirname "$0")/.."
cp AGENTS.md .clinerules
cp AGENTS.md .github/copilot-instructions.md
echo "Synced AGENTS.md -> .clinerules, .github/copilot-instructions.md"
