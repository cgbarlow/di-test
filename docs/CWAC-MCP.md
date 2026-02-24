# CWAC MCP Server — Technical Reference

The CWAC MCP server wraps the [Centralised Web Accessibility Checker](https://github.com/GOVTNZ/cwac) as an MCP server, exposing 6 tools for scan lifecycle management.

## Architecture

```
Claude Code
    |
    v
+----------------+     +----------------+     +----------------+
|  CWAC MCP      |---->|  Subprocess    |---->|    CWAC        |
|  Server        |     |  Runner        |     |  (cwac.py)     |
|  (FastMCP)     |     |                |     |                |
+----------------+     +----------------+     +----------------+
    |                                              |
    v                                              v
+----------------+                        +----------------+
| Scan Registry  |                        |  Results CSV   |
| (in-memory)    |                        |  files         |
+----------------+                        +----------------+
    |                                              |
    v                                              v
+----------------+                        +----------------+
|Config Builder  |                        |Result Reader   |
| (temp JSON)    |                        | (CSV parser)   |
+----------------+                        +----------------+
```

The server runs CWAC as a **subprocess** with `cwd=/workspaces/cwac` rather than importing it directly. This avoids modifying CWAC's source code and handles its reliance on relative paths (`./config/`, `./base_urls/`, `./results/`). See [ADR-002](adr/ADR-002-subprocess-vs-direct-import.md) for the full rationale.

## MCP Tools

| Tool | Description |
|------|-------------|
| `cwac_scan` | Start a CWAC accessibility scan. Accepts URLs, audit name, plugin toggles, crawl depth, and viewport sizes. Returns a scan ID for tracking. |
| `cwac_scan_status` | Check scan status (running/complete/failed), elapsed time, and recent output. |
| `cwac_get_results` | Retrieve scan results with optional filters by audit type, impact level, and row limit. |
| `cwac_get_summary` | Get aggregated summary: total issues, breakdown by audit type, axe impact distribution, top violations. |
| `cwac_list_scans` | List all active and historical scan result directories. |
| `cwac_generate_report` | Run CWAC's report exporter to generate leaderboard CSVs from scan results. |

## Usage Examples

**Run a basic accessibility scan:**
```
Scan https://www.example.govt.nz for accessibility issues using CWAC
```

**Scan multiple URLs with specific settings:**
```
Run a CWAC scan on these URLs with max 10 pages per domain:
- https://www.site1.govt.nz
- https://www.site2.govt.nz
```

**Check scan progress:**
```
What's the status of the CWAC scan?
```

**Get a summary of findings:**
```
Show me a summary of the CWAC scan results
```

**Filter results by severity:**
```
Show me only the critical axe-core issues from the scan
```

**Generate a report:**
```
Generate a leaderboard report from the CWAC scan results
```

## Scan Lifecycle

1. **Initiate** — `cwac_scan` builds config, writes base URLs CSV, launches CWAC subprocess
2. **Monitor** — `cwac_scan_status` polls the subprocess for progress
3. **Retrieve** — `cwac_get_results` or `cwac_get_summary` reads result CSVs
4. **Report** — `cwac_generate_report` runs the export pipeline

Scans are non-blocking: `cwac_scan` returns immediately with a scan ID, and you can check status while the scan runs. See [ADR-003](adr/ADR-003-scan-lifecycle-management.md) for the lifecycle design.

## Available Plugins

| Plugin | Key | Default |
|--------|-----|---------|
| Axe-core audit | `axe_core_audit` | Enabled |
| Language audit | `language_audit` | Enabled |
| Reflow audit | `reflow_audit` | Enabled |
| Focus indicator audit | `focus_indicator_audit` | Disabled |
| Screenshot audit | `screenshot_audit` | Disabled |
| Element audit | `element_audit` | Disabled |

## How It Works

1. You prompt Claude Code to run a CWAC scan
2. The MCP server generates a config JSON and base URLs CSV
3. CWAC runs as a subprocess in its own directory
4. The scan registry tracks progress via subprocess polling
5. Results are read from CWAC's CSV output files
6. Summaries and reports are generated on demand

## Fallback Mode (axe-core only)

When CWAC's chromedriver is unavailable or incompatible with the host architecture (e.g. ARM64 / Apple Silicon), the server automatically falls back to running axe-core directly via Playwright.

### How It Works

At server startup, `environment_check.py` probes for CWAC dependencies:
- If CWAC + chromedriver + selenium are available → **Full mode (`cwac`)**
- If Playwright + axe-core are available → **Fallback mode (`axe-only`)**

### Architecture (Fallback Mode)

```
Claude Code
    |
    v
+----------------+     +----------------+     +------------------+
|  CWAC MCP      |---->|  Scanner       |---->|  axe_scanner.py  |
|  Server        |     |  Runner        |     |  (Playwright +   |
|  (FastMCP)     |     |                |     |   axe-core)      |
+----------------+     +----------------+     +------------------+
    |                                              |
    v                                              v
+----------------+                        +------------------+
| Scan Registry  |                        | axe_core_audit   |
| (in-memory)    |                        | .csv (same       |
+----------------+                        | format as CWAC)  |
    |                                     +------------------+
    v                                              |
+----------------+                                 v
|Config Builder  |                        +------------------+
| (axe config)   |                        |Result Reader     |
+----------------+                        | (CSV parser)     |
                                          +------------------+
```

### What's Different

| Aspect | Full mode (CWAC) | Fallback mode (axe-only) |
|--------|-----------------|------------------------|
| Engine | CWAC subprocess | Playwright + axe-core |
| Audit types | All CWAC plugins | axe-core only |
| Architecture | x86-64 only | Any (ARM64, x86-64, etc.) |
| Results directory | `{CWAC_PATH}/results/` | `{PROJECT_ROOT}/output/` |
| CSV format | CWAC's 20-column format | Same 20-column format |
| Downstream tools | All work | All work (identical CSV) |

### What's the Same

- All 6 MCP tools work identically
- Tool responses include `scan_mode` so you know which engine ran
- CSV output format is identical (result_reader, report_generator, templates all work)
- Scan lifecycle (initiate → monitor → retrieve → report) is unchanged

See [ADR-007](adr/ADR-007-playwright-fallback.md) for the decision rationale and [SPEC-007-A](specs/SPEC-007-A-axe-scanner.md) for the technical specification.
