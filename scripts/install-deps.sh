#!/usr/bin/env bash
# install-deps.sh — Install dependencies for the di-test plugin.
# Called by the SessionStart hook. Designed to be idempotent.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CWAC_INSTALL_DIR="${HOME}/.local/share/di-test/cwac"

echo "[di-test] Checking dependencies..."

# ------------------------------------------------------------------
# Python dependencies (must come first — playwright package needed later)
# ------------------------------------------------------------------
if ! python3 -c "import mcp" 2>/dev/null || ! python3 -c "import playwright" 2>/dev/null; then
    echo "[di-test] Installing Python dependencies..."
    pip install -q -r "$PROJECT_ROOT/cwac_mcp/requirements.txt"
else
    echo "[di-test] Python dependencies already installed."
fi

# ------------------------------------------------------------------
# Node.js dependencies (must come before Playwright browser install)
# ------------------------------------------------------------------
if [ ! -d "$PROJECT_ROOT/node_modules/playwright" ] || [ ! -d "$PROJECT_ROOT/node_modules/axe-core" ]; then
    echo "[di-test] Installing Node.js dependencies..."
    cd "$PROJECT_ROOT" && npm install --silent 2>/dev/null || echo "[di-test] WARNING: npm install failed (non-fatal)."
else
    echo "[di-test] Node.js dependencies already installed."
fi

# ------------------------------------------------------------------
# Playwright browser (must come after both pip install and npm install)
# ------------------------------------------------------------------
if ! python3 -c "
from playwright.sync_api import sync_playwright
p = sync_playwright().start()
try:
    b = p.chromium.launch(headless=True)
    b.close()
finally:
    p.stop()
" 2>/dev/null; then
    echo "[di-test] Installing Playwright Chromium browser..."
    python3 -m playwright install chromium 2>/dev/null || echo "[di-test] WARNING: Playwright browser install failed (non-fatal)."
else
    echo "[di-test] Playwright browser already installed."
fi

# ------------------------------------------------------------------
# CWAC installation (optional — fallback mode available without CWAC)
# ------------------------------------------------------------------
CWAC_PATH="${CWAC_PATH:-}"

# Discovery chain: env var → sibling → /workspaces/cwac → ~/.local/share/di-test/cwac
if [ -z "$CWAC_PATH" ]; then
    SIBLING="$(dirname "$PROJECT_ROOT")/cwac"
    if [ -d "$SIBLING" ] && [ -f "$SIBLING/cwac.py" ]; then
        CWAC_PATH="$SIBLING"
    elif [ -d "/workspaces/cwac" ] && [ -f "/workspaces/cwac/cwac.py" ]; then
        CWAC_PATH="/workspaces/cwac"
    elif [ -d "$CWAC_INSTALL_DIR" ] && [ -f "$CWAC_INSTALL_DIR/cwac.py" ]; then
        CWAC_PATH="$CWAC_INSTALL_DIR"
    fi
fi

if [ -n "$CWAC_PATH" ] && [ -f "$CWAC_PATH/cwac.py" ]; then
    echo "[di-test] CWAC found at: $CWAC_PATH"
    echo "[di-test] Full mode available: All audit plugins (axe-core, language, readability, etc.)"
else
    echo "[di-test] CWAC not found. Attempting to clone from GitHub..."
    mkdir -p "$(dirname "$CWAC_INSTALL_DIR")"
    if git clone --depth 1 https://github.com/GOVTNZ/cwac.git "$CWAC_INSTALL_DIR" 2>/dev/null; then
        CWAC_PATH="$CWAC_INSTALL_DIR"
        echo "[di-test] CWAC cloned to: $CWAC_PATH"

        # Install CWAC Python dependencies
        echo "[di-test] Installing CWAC Python dependencies..."
        pip install -q -r "$CWAC_PATH/requirements.txt" 2>/dev/null || echo "[di-test] WARNING: CWAC Python deps failed (non-fatal)."

        # Install CWAC Node dependencies + Chrome
        echo "[di-test] Installing CWAC Node dependencies and Chrome..."
        cd "$CWAC_PATH" && npm install --silent 2>/dev/null || echo "[di-test] WARNING: CWAC Node deps failed (non-fatal)."

        echo "[di-test] CWAC installation complete."
    else
        echo "[di-test] WARNING: Could not clone CWAC. Falling back to axe-core only mode."
        echo "[di-test] Fallback mode: axe-core accessibility scanning via Playwright."
    fi
fi

# Export for the MCP server process to discover
if [ -n "$CWAC_PATH" ]; then
    export CWAC_PATH
fi

echo "[di-test] Dependency check complete."
