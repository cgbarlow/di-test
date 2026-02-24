# SPEC-006-A: Installation Pipeline

| Field           | Value                                |
|-----------------|--------------------------------------|
| **Parent ADR**  | ADR-006 (Dependency Management)      |
| **Version**     | A (initial)                          |
| **Status**      | Accepted                             |
| **Date**        | 2026-02-24                           |

## Overview

This specification defines the installation pipeline that bootstraps all dependencies required by the di-test plugin. The pipeline is triggered automatically by a Claude Code SessionStart hook and handles Python package installation, CWAC path discovery, Node.js dependency setup, and verification checks.

The pipeline is designed around three principles:

1. **Zero-friction startup** -- no manual steps required after cloning the repository.
2. **Idempotency** -- repeated runs produce the same result without unnecessary work.
3. **Fail-fast with clear errors** -- missing dependencies are detected early with actionable messages.

---

## 1. SessionStart Hook

### 1.1 Trigger

The Claude Code SessionStart hook is configured in `.claude/settings.json`:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "command": "bash scripts/install-deps.sh",
        "timeout": 120
      }
    ]
  }
}
```

The hook fires automatically when Claude Code opens a new session in the di-test project directory. It runs before any MCP servers are started and before the user's first prompt is processed.

### 1.2 Execution

The hook invokes `scripts/install-deps.sh` as a bash process. The script:

1. Runs with the project root (`/workspaces/di-test`) as its working directory.
2. Inherits the session's environment variables, including any user-set `CWAC_PATH`.
3. Writes progress messages to stdout, which are visible in the Claude Code session log.
4. Exits with code 0 on success or non-zero on failure.

### 1.3 Idempotency

The script is safe to run multiple times. Each installation step checks whether work has already been done before proceeding:

| Step                       | Skip condition                                                  |
|----------------------------|-----------------------------------------------------------------|
| Python packages            | `pip show <package>` succeeds for all packages in requirements.txt |
| Playwright browsers        | `npx playwright install --dry-run` reports no downloads needed  |
| CWAC_PATH validation       | Path already resolved and `cwac.py` exists at target            |

On a warm start (all dependencies present), the script completes in under 2 seconds.

### 1.4 Timeout

The hook has a 120-second timeout. If the script exceeds this (e.g., due to a slow network during first-time pip install), the session starts but a warning is displayed. The MCP server will fail to start if critical dependencies are missing, prompting the user to run the script manually.

---

## 2. install-deps.sh Script

### 2.1 Script Location

```
scripts/install-deps.sh
```

The script is executable (`chmod +x`) and uses a bash shebang (`#!/usr/bin/env bash`).

### 2.2 What It Installs

The script handles three categories of dependencies:

#### 2.2.1 Python Packages

```bash
pip install -r cwac_mcp/requirements.txt --quiet
```

This installs the packages listed in `cwac_mcp/requirements.txt`:

| Package       | Purpose                                          |
|---------------|--------------------------------------------------|
| `mcp[cli]`    | MCP SDK with CLI entry point for stdio transport |
| `python-docx` | Word document generation for accessibility reports |
| `jinja2`      | Template engine for report HTML/document rendering |

The `--quiet` flag suppresses verbose output during normal operation. On first install, pip resolves and downloads all transitive dependencies.

#### 2.2.2 Node.js Packages

```bash
npm install --prefer-offline
npx playwright install chromium
```

The `npm install` command installs dependencies from `package.json`, primarily `@playwright/test`. The `npx playwright install chromium` command downloads the Chromium browser binary required by Playwright.

#### 2.2.3 CWAC Path Validation

The script validates that CWAC is accessible (see Section 3) but does **not** install CWAC itself. If CWAC is not found, the script prints a clear error message with instructions.

### 2.3 Error Handling

The script uses `set -e` to exit on the first error. Each major step is wrapped with descriptive output:

```bash
echo "[install-deps] Installing Python dependencies..."
pip install -r cwac_mcp/requirements.txt --quiet || {
    echo "[install-deps] ERROR: Failed to install Python dependencies."
    exit 1
}
echo "[install-deps] Python dependencies installed."
```

Exit codes:

| Code | Meaning                                     |
|------|---------------------------------------------|
| 0    | All dependencies installed and verified     |
| 1    | Python dependency installation failed       |
| 2    | Node.js dependency installation failed      |
| 3    | CWAC not found at any expected location     |

### 2.4 Skip-if-Installed Logic

To avoid unnecessary pip and npm operations on subsequent runs, the script checks for key marker packages before invoking package managers:

```bash
# Skip Python install if mcp is already importable
python -c "import mcp" 2>/dev/null && \
python -c "import docx" 2>/dev/null && \
python -c "import jinja2" 2>/dev/null && {
    echo "[install-deps] Python dependencies already installed, skipping."
} || {
    echo "[install-deps] Installing Python dependencies..."
    pip install -r cwac_mcp/requirements.txt --quiet
}
```

This pattern ensures that warm starts (all packages present) complete quickly while cold starts (fresh environment) install everything needed.

---

## 3. CWAC_PATH Discovery

### 3.1 Discovery Chain

The CWAC installation path is resolved using a three-step fallback chain, evaluated in order:

| Priority | Source                        | Resolution                                         |
|----------|-------------------------------|----------------------------------------------------|
| 1        | `CWAC_PATH` environment var   | Use the value of `$CWAC_PATH` directly             |
| 2        | Sibling directory             | Resolve `../cwac` relative to the plugin root      |
| 3        | Hardcoded fallback            | `/workspaces/cwac`                                 |

The first path that passes validation (see Section 3.2) is used. If none pass, the script fails with exit code 3.

### 3.2 Validation

A candidate CWAC path is valid if and only if:

1. The directory exists.
2. The file `cwac.py` exists within the directory.
3. The directory contains a `config/` subdirectory.

```bash
validate_cwac_path() {
    local candidate="$1"
    [[ -d "$candidate" ]] && \
    [[ -f "$candidate/cwac.py" ]] && \
    [[ -d "$candidate/config" ]]
}
```

### 3.3 Runtime Resolution

The `cwac_mcp/__init__.py` module exports the resolved `CWAC_PATH` as a module-level constant. All other modules (`config_builder.py`, `cwac_runner.py`, `result_reader.py`) import this value rather than performing their own discovery.

The current implementation uses a hardcoded path:

```python
CWAC_PATH = "/workspaces/cwac"
```

The full discovery chain will be implemented as:

```python
import os

def _discover_cwac_path() -> str:
    """Resolve the CWAC installation directory."""
    # Priority 1: Environment variable
    env_path = os.environ.get("CWAC_PATH")
    if env_path and _is_valid_cwac(env_path):
        return env_path

    # Priority 2: Sibling directory
    plugin_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sibling_path = os.path.join(os.path.dirname(plugin_root), "cwac")
    if _is_valid_cwac(sibling_path):
        return sibling_path

    # Priority 3: Hardcoded fallback
    fallback_path = "/workspaces/cwac"
    if _is_valid_cwac(fallback_path):
        return fallback_path

    raise RuntimeError(
        "CWAC installation not found. Set the CWAC_PATH environment variable "
        "to the directory containing cwac.py, or clone CWAC as a sibling directory."
    )

def _is_valid_cwac(path: str) -> bool:
    """Check whether a directory looks like a valid CWAC installation."""
    return (
        os.path.isdir(path)
        and os.path.isfile(os.path.join(path, "cwac.py"))
        and os.path.isdir(os.path.join(path, "config"))
    )

CWAC_PATH = _discover_cwac_path()
```

### 3.4 Environment Variable Override

Users can override the discovery chain entirely by setting `CWAC_PATH` in their shell environment or in a `.env` file:

```bash
export CWAC_PATH=/home/user/projects/cwac
```

This is the recommended approach for non-standard directory layouts.

---

## 4. Python Dependencies

### 4.1 requirements.txt Contents

The file `cwac_mcp/requirements.txt` declares all Python packages required by the CWAC MCP server:

```
mcp[cli]
python-docx
jinja2
```

| Package       | Version Constraint | Purpose                                                      |
|---------------|--------------------|--------------------------------------------------------------|
| `mcp[cli]`    | Unpinned (latest)  | MCP SDK with the `cli` extra for stdio server support        |
| `python-docx` | Unpinned (latest)  | Create and modify `.docx` Word documents for reports         |
| `jinja2`      | Unpinned (latest)  | Template rendering for HTML and document-based reports       |

### 4.2 Transitive Dependencies

The `mcp[cli]` package brings in several transitive dependencies, including:

- `pydantic` -- data validation and settings management
- `httpx` -- async HTTP client (used internally by the MCP SDK)
- `anyio` -- async compatibility layer
- `click` -- CLI framework (from the `[cli]` extra)

These are managed by pip automatically and do not need to be declared in `requirements.txt`.

### 4.3 Virtual Environment Support

The install script does not create or manage a virtual environment. It installs packages into whatever Python environment is currently active:

- If a virtualenv is active, packages install there.
- If no virtualenv is active, packages install into the system Python (or user site-packages if `--user` is in pip config).
- In GitHub Codespaces, the default Python environment is a system-level install with write permissions, so no virtualenv is needed.

For local development, users are encouraged to create their own virtualenv before opening the project in Claude Code:

```bash
python -m venv .venv
source .venv/bin/activate
```

The SessionStart hook will then install into the active virtualenv.

### 4.4 Dependency Conflicts

The unpinned version strategy prioritises simplicity over strict reproducibility. If version conflicts arise (e.g., another project in the same environment requires an incompatible `pydantic` version), the recommended resolution is to use a dedicated virtualenv for the di-test project.

---

## 5. Node.js Dependencies

### 5.1 Playwright Installation

Playwright is required for two purposes:

1. **Playwright MCP server** -- the `@playwright/mcp` package provides browser automation tools to Claude Code, configured in `.mcp.json`.
2. **Visual pattern scanner** -- the di-test visual pattern detection features use Playwright for browser rendering.

### 5.2 Package Management

Node.js dependencies are declared in `package.json`:

```json
{
  "dependencies": {
    "@playwright/test": "^1.58.2"
  }
}
```

The install script runs:

```bash
npm install --prefer-offline
```

The `--prefer-offline` flag uses cached packages when available, reducing install time on subsequent runs.

### 5.3 Browser Binaries

Playwright requires browser binaries (Chromium, Firefox, WebKit) to be downloaded separately from the npm package. The install script installs Chromium specifically:

```bash
npx playwright install chromium
```

Only Chromium is installed because:

- The Playwright MCP server uses Chromium by default.
- Chromium is the browser used for CWAC's axe-core audits.
- Installing all browsers would add significant download time and disk usage.

### 5.4 Separation from Python

Node.js and Python dependencies are intentionally kept separate:

- Python dependencies are in `cwac_mcp/requirements.txt` and installed via pip.
- Node.js dependencies are in `package.json` and installed via npm.
- There is no cross-language dependency manager.

This separation reflects the distinct runtime environments: the CWAC MCP server is Python, while the Playwright MCP server and visual scanner are Node.js.

---

## 6. Verification

### 6.1 Health Checks

After installation, the script runs verification checks to confirm that all critical dependencies are available:

```bash
# Verify Python dependencies
python -c "import mcp; import docx; import jinja2; print('[install-deps] Python OK')"

# Verify Playwright
npx playwright --version && echo "[install-deps] Playwright OK"

# Verify CWAC path
[[ -f "${CWAC_PATH}/cwac.py" ]] && echo "[install-deps] CWAC OK"
```

All three checks must pass for the script to exit with code 0.

### 6.2 Missing Dependency Errors

When a dependency is missing at runtime, the following errors are produced:

| Missing Dependency | Error Location          | Error Message                                                |
|--------------------|-------------------------|--------------------------------------------------------------|
| `mcp[cli]`         | Server startup          | `ModuleNotFoundError: No module named 'mcp'`                 |
| `python-docx`      | Report generation       | `ModuleNotFoundError: No module named 'docx'`                |
| `jinja2`           | Report generation       | `ModuleNotFoundError: No module named 'jinja2'`              |
| Playwright binary  | Playwright MCP startup  | `Executable doesn't exist at /path/to/chromium`              |
| CWAC               | MCP server startup      | `RuntimeError: CWAC installation not found. Set the CWAC_PATH environment variable...` |

### 6.3 Manual Recovery

If the SessionStart hook fails or times out, users can run the installation manually:

```bash
bash scripts/install-deps.sh
```

For individual components:

```bash
# Python only
pip install -r cwac_mcp/requirements.txt

# Node.js only
npm install && npx playwright install chromium

# Verify CWAC
ls /workspaces/cwac/cwac.py
```

---

## Related Specifications

| Spec ID    | Relationship | Title                        |
|------------|-------------|------------------------------|
| SPEC-001-A | Related     | MCP Tool Definitions         |
| SPEC-002-A | Related     | Subprocess Execution Model   |

## Changelog

| Version | Date       | Author        | Changes                          |
|---------|------------|---------------|----------------------------------|
| A       | 2026-02-24 | Chris Barlow  | Initial specification            |
