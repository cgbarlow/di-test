#!/usr/bin/env bash
# install-deps.sh — Install dependencies for the di-test plugin.
# Called by the SessionStart hook. Designed to be idempotent.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "[di-test] Checking dependencies..."

# ------------------------------------------------------------------
# Python dependencies
# ------------------------------------------------------------------
if ! python3 -c "import mcp" 2>/dev/null; then
    echo "[di-test] Installing Python dependencies..."
    pip install -q -r "$PROJECT_ROOT/cwac_mcp/requirements.txt"
else
    echo "[di-test] Python dependencies already installed."
fi

# ------------------------------------------------------------------
# Node.js dependencies (Playwright)
# ------------------------------------------------------------------
if [ ! -d "$PROJECT_ROOT/node_modules/playwright" ]; then
    echo "[di-test] Installing Node.js dependencies..."
    cd "$PROJECT_ROOT" && npm install --silent
else
    echo "[di-test] Node.js dependencies already installed."
fi

# ------------------------------------------------------------------
# CWAC availability check
# ------------------------------------------------------------------
CWAC_PATH="${CWAC_PATH:-}"

if [ -z "$CWAC_PATH" ]; then
    # Try sibling directory
    SIBLING="$(dirname "$PROJECT_ROOT")/cwac"
    if [ -d "$SIBLING" ] && [ -f "$SIBLING/cwac.py" ]; then
        CWAC_PATH="$SIBLING"
    elif [ -d "/workspaces/cwac" ] && [ -f "/workspaces/cwac/cwac.py" ]; then
        CWAC_PATH="/workspaces/cwac"
    fi
fi

if [ -n "$CWAC_PATH" ] && [ -d "$CWAC_PATH" ]; then
    echo "[di-test] CWAC found at: $CWAC_PATH"
else
    echo "[di-test] WARNING: CWAC not found. CWAC MCP tools will not be available."
    echo "[di-test] Set CWAC_PATH environment variable or install CWAC as a sibling directory."
fi

echo "[di-test] Dependency check complete."
