# SPEC-007-A: axe-core Scanner (Playwright Fallback)

| Field | Value |
|-------|-------|
| **Status** | Accepted |
| **Date** | 2026-02-24 |
| **ADR** | ADR-007 |

## 1. Overview

This specification defines the Playwright + axe-core fallback scanner that runs when CWAC is unavailable. The scanner injects axe-core JavaScript into pages via Playwright, collects violations, and writes results to CSV in the same column format as CWAC's `axe_core_audit.csv`.

## 2. Environment Check (`environment_check.py`)

### 2.1 Purpose

Detect whether the full CWAC suite or the axe-core-only fallback should be used.

### 2.2 Interface

```python
def check_environment() -> dict:
    """Returns:
        {
            "mode": "cwac" | "axe-only",
            "cwac_available": bool,
            "cwac_path": str | None,
            "chromedriver_ok": bool,
            "playwright_available": bool,
            "axe_core_available": bool,
            "message": str
        }
    """
```

### 2.3 Detection Logic

1. **CWAC path:** Use existing `_discover_cwac_path()` logic. Check `cwac.py` exists.
2. **chromedriver:** Check chromedriver binary exists in CWAC directory AND is compatible with host architecture. Compare ELF/Mach-O header or `platform.machine()` against binary.
3. **Selenium:** Check `import selenium` succeeds.
4. **Playwright:** Check `import playwright` succeeds.
5. **axe-core:** Check `node_modules/axe-core/axe.min.js` exists.

### 2.4 Mode Selection

- `mode = "cwac"` if CWAC path valid AND chromedriver OK AND selenium importable
- `mode = "axe-only"` if playwright importable AND axe-core JS exists
- Error if neither mode is possible

## 3. axe-core Scanner (`axe_scanner.py`)

### 3.1 Invocation

```bash
python axe_scanner.py <config.json>
```

Runs as a standalone subprocess (consistent with ADR-002 subprocess model).

### 3.2 Config Format

```json
{
    "audit_name": "my_scan",
    "urls": ["https://example.com"],
    "max_links_per_domain": 10,
    "viewport_sizes": {
        "medium": {"width": 1280, "height": 800}
    },
    "output_dir": "/workspaces/di-test/output/20260224_100000_my_scan",
    "axe_core_path": "/workspaces/di-test/node_modules/axe-core/axe.min.js"
}
```

### 3.3 Scan Process

1. Read config JSON from the provided path
2. Launch Playwright Chromium (sync API)
3. For each URL in config:
   a. Navigate to URL
   b. For each viewport size: resize browser, inject axe-core JS, run `axe.run()`, collect violations
   c. Crawl same-domain links up to `max_links_per_domain`
4. Flatten all violations into CSV rows
5. Write `axe_core_audit.csv` to the output directory
6. Print progress to stdout

### 3.4 CSV Column Format

The output CSV must match CWAC's `axe_core_audit.csv` columns exactly:

```
organisation,sector,page_title,base_url,url,viewport_size,audit_id,page_id,
audit_type,issue_id,description,target,num_issues,help,helpUrl,id,impact,
html,tags,best-practice
```

### 3.5 Violation Flattening

Each axe-core violation node becomes one CSV row:

| CSV Column | axe-core Source |
|------------|----------------|
| `organisation` | "MCP Scan" (constant) |
| `sector` | "MCP" (constant) |
| `page_title` | `document.title` |
| `base_url` | First URL from config |
| `url` | Current page URL |
| `viewport_size` | Current viewport dict as string |
| `audit_id` | `{page_index}_{viewport_name}` |
| `page_id` | Sequential page index |
| `audit_type` | "AxeCoreAudit" |
| `issue_id` | Sequential issue index |
| `description` | `violation.description` |
| `target` | `node.target` joined with `,` |
| `num_issues` | "1" (one row per node) |
| `help` | `violation.help` |
| `helpUrl` | `violation.helpUrl` |
| `id` | `violation.id` |
| `impact` | `violation.impact` |
| `html` | `node.html` |
| `tags` | `violation.tags` joined with `,` |
| `best-practice` | "Yes" if `best-practice` in tags, else "No" |

### 3.6 Link Crawling

- Extract same-domain `<a href>` links from each page
- Normalize URLs (strip fragments, resolve relative)
- Deduplicate
- Stop at `max_links_per_domain` per base URL domain

## 4. Scanner Runner (`scanner_runner.py`)

### 4.1 Purpose

Launch `axe_scanner.py` as a subprocess, analogous to `cwac_runner.py`.

### 4.2 Interface

```python
def start_scanner(config_path: str) -> subprocess.Popen:
    """Launch axe_scanner.py as a subprocess.

    Args:
        config_path: Absolute path to the config JSON file.

    Returns:
        Popen process handle.
    """
```

## 5. Config Builder Extension

### 5.1 New Function

```python
def build_axe_config(
    scan_id: str,
    audit_name: str,
    urls: list[str],
    max_links_per_domain: int | None = None,
    viewport_sizes: dict | None = None,
) -> tuple[str, str]:
    """Build a config for the axe-core fallback scanner.

    Returns:
        (config_path, output_dir) - absolute paths
    """
```

### 5.2 Differences from `build_config()`

- Does NOT read CWAC's `config_default.json`
- Does NOT write to CWAC directories
- Writes config JSON to project's `output/` directory
- Creates timestamped output directory for results
- Config format matches Section 3.2 above

## 6. Server Routing

At server startup, `check_environment()` determines `SCAN_MODE`. The `cwac_scan` tool routes to the appropriate runner:

- `mode == "cwac"`: existing `build_config() → start_cwac()` flow
- `mode == "axe-only"`: `build_axe_config() → start_scanner()` flow

All tool responses include `scan_mode` so the user knows which engine ran.

## 7. Results Discovery

### 7.1 Dual Results Root

- CWAC mode: results in `{CWAC_PATH}/results/`
- Fallback mode: results in `{PROJECT_ROOT}/output/`

`list_scan_results()` and `_discover_results_dir()` search both locations.

## 8. Test Plan

### 8.1 Unit Tests (`test_environment_check.py`)

- Returns `cwac` mode when all CWAC deps available
- Returns `axe-only` mode when CWAC unavailable but Playwright available
- Correctly detects chromedriver architecture mismatch
- Returns appropriate error when neither mode possible

### 8.2 Unit Tests (`test_axe_scanner.py`)

- `flatten_violations()` correctly maps axe-core JSON to CSV rows
- `write_csv()` produces correct column headers
- `extract_links()` filters to same-domain only
- Handles empty violations list
- Handles pages with no violations

### 8.3 Integration Tests

- `build_axe_config()` creates valid config JSON
- Scanner subprocess launches and exits cleanly
- CSV output has correct 20-column format
- `result_reader` can parse fallback CSV
- `get_summary()` works on fallback results
