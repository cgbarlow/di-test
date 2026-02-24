# Manual Setup

This guide covers setting up di-test without the Claude Code plugin system. If you're using the plugin, dependencies are installed automatically — you don't need this.

## Prerequisites

- Python 3.10+
- Node.js v18+
- [CWAC](https://github.com/GOVTNZ/cwac) installed at a discoverable location (optional — fallback mode works without it)

## Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/cgbarlow/di-test.git
   cd di-test
   ```
2. Install Python dependencies:
   ```bash
   pip install -r cwac_mcp/requirements.txt
   ```
3. Install Node.js dependencies (Playwright + axe-core):
   ```bash
   npm install
   ```
4. Install the Playwright Chromium browser:
   ```bash
   npx playwright install --with-deps chromium
   ```
5. (Optional) Install [CWAC](https://github.com/GOVTNZ/cwac) for full mode:
   ```bash
   git clone https://github.com/GOVTNZ/cwac.git ../cwac
   cd ../cwac && pip install -r requirements.txt && npm install && cd -
   ```
   Or set `CWAC_PATH` to an existing CWAC installation. Without CWAC, the scanner runs in axe-core only fallback mode.
6. Both MCP servers are configured in `.mcp.json`. Claude Code will discover them automatically.

## Running Tests

```bash
pytest tests/
```

The test suite includes 103 pytest tests across 9 test files covering environment detection, axe-core scanner, config builder, result reader, scan registry, report generation, templates, and plugin manifest.

## Verifying the Environment

You can check which scanning mode is available:

```python
from cwac_mcp.environment_check import check_environment
result = check_environment()
print(result["mode"])     # "cwac" or "axe-only"
print(result["message"])  # Human-readable summary
```
