#!/usr/bin/env bash
# install-deps.sh — Install dependencies for the di-test plugin.
# Called by the SessionStart hook. Designed to be idempotent.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CWAC_INSTALL_DIR="${HOME}/.local/share/di-test/cwac"

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
# CWAC installation
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
else
    echo "[di-test] CWAC not found. Cloning from GitHub..."
    mkdir -p "$(dirname "$CWAC_INSTALL_DIR")"
    git clone --depth 1 https://github.com/GOVTNZ/cwac.git "$CWAC_INSTALL_DIR"
    CWAC_PATH="$CWAC_INSTALL_DIR"
    echo "[di-test] CWAC cloned to: $CWAC_PATH"

    # Install CWAC Python dependencies
    echo "[di-test] Installing CWAC Python dependencies..."
    pip install -q -r "$CWAC_PATH/requirements.txt"

    # Install CWAC Node dependencies + Chrome
    echo "[di-test] Installing CWAC Node dependencies and Chrome..."
    cd "$CWAC_PATH" && npm install --silent

    echo "[di-test] CWAC installation complete."
fi

# Export for the MCP server process to discover
export CWAC_PATH

echo "[di-test] Dependency check complete."
