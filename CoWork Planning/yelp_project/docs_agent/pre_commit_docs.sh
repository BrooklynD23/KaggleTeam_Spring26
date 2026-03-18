#!/usr/bin/env bash
# pre_commit_docs.sh — Claude Code PreToolUse hook for the Intern Documentation Agent
#
# This script receives JSON on stdin from Claude Code's hook system.
# It checks if the Bash command is a git commit. If so, it generates
# a changes manifest for the documentation agent to process.
#
# For non-commit Bash commands, it exits 0 (allow) immediately.

set -euo pipefail

# Read the JSON input from Claude Code
INPUT=$(cat /dev/stdin 2>/dev/null || echo '{}')

# Extract the bash command from the tool input
COMMAND=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('tool_input', {}).get('command', ''))
except:
    print('')
" 2>/dev/null || echo "")

# Only act on git commit commands — let everything else pass through
if ! echo "$COMMAND" | grep -q '^git commit'; then
    exit 0
fi

# --- This is a git commit. Generate the documentation manifest. ---

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DOCS_DIR="${PROJECT_ROOT}/yelp_project/docs/intern"

# Ensure docs directories exist
mkdir -p "${DOCS_DIR}/code" "${DOCS_DIR}/workflows" "${DOCS_DIR}/config" "${DOCS_DIR}/decisions"

# Get staged files
STAGED_FILES=$(git diff --cached --name-only 2>/dev/null || echo "")

if [ -z "$STAGED_FILES" ]; then
    # No staged files — allow the commit (it will fail on its own)
    exit 0
fi

# Categorize staged files
PY_COUNT=0
YAML_COUNT=0
MD_COUNT=0
OTHER_COUNT=0

while IFS= read -r file; do
    [ -z "$file" ] && continue
    case "$file" in
        *.py)              PY_COUNT=$((PY_COUNT + 1)) ;;
        *.yaml|*.yml|*.json) YAML_COUNT=$((YAML_COUNT + 1)) ;;
        *.md)              MD_COUNT=$((MD_COUNT + 1)) ;;
        *)                 OTHER_COUNT=$((OTHER_COUNT + 1)) ;;
    esac
done <<< "$STAGED_FILES"

TOTAL=$((PY_COUNT + YAML_COUNT + MD_COUNT + OTHER_COUNT))

# Write manifest for the documentation agent
MANIFEST="${DOCS_DIR}/.changes_manifest.json"
cat > "$MANIFEST" << MANIFEST_EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "total_staged_files": ${TOTAL},
  "categories": {
    "python": ${PY_COUNT},
    "config": ${YAML_COUNT},
    "documentation": ${MD_COUNT},
    "other": ${OTHER_COUNT}
  },
  "staged_files": $(echo "$STAGED_FILES" | python3 -c "
import sys, json
files = [line.strip() for line in sys.stdin if line.strip()]
print(json.dumps(files))
" 2>/dev/null || echo '[]')
}
MANIFEST_EOF

# Print info to stderr (visible to user, does not affect hook decision)
echo "HOOK:intern-docs: ${TOTAL} staged files (${PY_COUNT} py, ${YAML_COUNT} config, ${MD_COUNT} md, ${OTHER_COUNT} other)" >&2
echo "HOOK:intern-docs: Manifest at ${MANIFEST}" >&2
echo "HOOK:intern-docs: Run the intern-docs agent to generate documentation before committing." >&2

# Allow the commit to proceed — the agent generates docs as a separate step
exit 0
