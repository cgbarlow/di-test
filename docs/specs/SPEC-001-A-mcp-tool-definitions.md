# SPEC-001-A: MCP Tool Definitions

| Field           | Value                                |
|-----------------|--------------------------------------|
| **Parent ADR**  | ADR-001 (CWAC MCP Integration Approach) |
| **Version**     | A (initial)                          |
| **Status**      | Draft                                |
| **Date**        | 2026-02-24                           |

## Overview

This specification defines the six MCP tools exposed by the CWAC MCP Server. Each tool definition includes its name, description, parameter schema, return schema, and behavioural details. Together these tools provide a complete scan lifecycle: initiation, monitoring, result retrieval, browsing, and reporting.

The tools are registered with the MCP server at startup and are discoverable by any MCP-compatible client (e.g., Claude Code). Parameter validation is performed by the MCP framework before the tool handler is invoked.

---

## Tool 1: `cwac_scan`

**Purpose:** Start a new CWAC accessibility scan.

### Description

Initiates a CWAC scan against one or more URLs. The tool generates the necessary configuration and input files, launches CWAC as a subprocess, and returns a scan ID for tracking.

### Parameters

| Parameter             | Type                          | Required | Default | Description                                                              |
|-----------------------|-------------------------------|----------|---------|--------------------------------------------------------------------------|
| `urls`                | `array` of `string`           | Yes      | --      | List of URLs to scan. Each URL becomes a row in the base URLs CSV.       |
| `audit_name`          | `string`                      | No       | Auto-generated from timestamp | Human-readable name for the scan.                    |
| `plugins`             | `object` (string -> boolean)  | No       | All enabled | Map of plugin names to enabled/disabled state. Known plugins: `axe_core_audit`, `html_validation`, `crawl_audit`, `seo_audit`. |
| `max_links_per_domain`| `integer`                     | No       | `50`    | Maximum number of links to follow per domain during crawling.            |
| `viewport_sizes`      | `object`                      | No       | CWAC defaults | Viewport dimensions for browser-based audits. Keys: `width`, `height`. |

### Return Value

```json
{
  "scan_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "config_path": "/workspaces/cwac/config/mcp_a1b2c3d4.json",
  "base_urls_dir": "/workspaces/cwac/base_urls/visit/mcp_a1b2c3d4/",
  "status": "started",
  "audit_name": "scan_2026-02-24_14-30-00"
}
```

### Behaviour

1. **Generate scan ID.** Create a UUID4 identifier for the scan.
2. **Read default config.** Load `/workspaces/cwac/config/config_default.json` as the base configuration.
3. **Override config fields.** Apply parameter overrides:
   - Set `base_urls_visit_path` to `./base_urls/visit/mcp_{scan_id}/`.
   - Set `audit_name` to the provided value or generate from timestamp.
   - Enable/disable plugins according to the `plugins` parameter.
   - Set `max_links_per_domain` if provided.
   - Set viewport sizes if provided.
4. **Write config file.** Save the modified config to `/workspaces/cwac/config/mcp_{scan_id}.json`.
5. **Create base URLs directory.** Create `/workspaces/cwac/base_urls/visit/mcp_{scan_id}/`.
6. **Write URLs CSV.** Write a `urls.csv` file with the header `organisation,url,sector` followed by one row per URL. The `organisation` field defaults to the domain name; the `sector` field defaults to `"unknown"`.
7. **Launch subprocess.** Execute `subprocess.Popen(["python", "cwac.py", "mcp_{scan_id}.json"], cwd="/workspaces/cwac", stdout=PIPE, stderr=PIPE)`.
8. **Register scan.** Create a `ScanRecord` in the scan registry with status `running`.
9. **Return immediately** with the scan ID and metadata.

### Error Conditions

| Condition                        | Response                                                        |
|----------------------------------|-----------------------------------------------------------------|
| Empty `urls` array               | Error: "At least one URL is required"                           |
| Invalid URL format               | Error: "Invalid URL: {url}"                                     |
| CWAC directory not found         | Error: "CWAC installation not found at /workspaces/cwac"        |
| Default config not found         | Error: "CWAC default config not found"                          |
| Subprocess fails to start        | Error: "Failed to start CWAC process: {details}"                |

---

## Tool 2: `cwac_scan_status`

**Purpose:** Check the status of a running or completed scan.

### Description

Polls the subprocess associated with a scan and returns its current status, elapsed time, and recent output.

### Parameters

| Parameter  | Type     | Required | Description                      |
|------------|----------|----------|----------------------------------|
| `scan_id`  | `string` | Yes      | The scan ID returned by `cwac_scan`. |

### Return Value

**While running:**

```json
{
  "scan_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "running",
  "elapsed_time": "2m 15s",
  "stdout_tail": "Processing https://example.com/about ...\nFound 12 links on page"
}
```

**When complete:**

```json
{
  "scan_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "complete",
  "elapsed_time": "5m 42s",
  "results_dir": "/workspaces/cwac/results/scan_2026-02-24_14-30-00_20260224_143542/",
  "exit_code": 0
}
```

**When failed:**

```json
{
  "scan_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "failed",
  "elapsed_time": "0m 12s",
  "exit_code": 1,
  "stderr": "FileNotFoundError: chromedriver not found"
}
```

### Behaviour

1. **Look up scan.** Find the `ScanRecord` in the registry by `scan_id`.
2. **Poll process.** Call `process.poll()` on the stored `Popen` object.
   - If `poll()` returns `None`: status is `running`. Read available stdout (non-blocking) and return the last 20 lines.
   - If `poll()` returns `0`: status is `complete`. Update the scan record with `end_time`. Trigger cleanup of temp files.
   - If `poll()` returns non-zero: status is `failed`. Capture full stderr. Update the scan record.
3. **Calculate elapsed time.** Compute the difference between `start_time` and now (or `end_time` if complete).
4. **Return status object.**

### Error Conditions

| Condition                  | Response                                    |
|----------------------------|---------------------------------------------|
| Unknown `scan_id`          | Error: "No scan found with ID: {scan_id}"   |

---

## Tool 3: `cwac_get_results`

**Purpose:** Retrieve detailed scan results with optional filtering.

### Description

Reads the CSV result files from a completed scan's results directory, converts them to JSON, and returns the data with optional filtering by audit type and impact level.

### Parameters

| Parameter    | Type     | Required | Default     | Description                                                         |
|--------------|----------|----------|-------------|---------------------------------------------------------------------|
| `scan_id`    | `string` | Yes      | --          | The scan ID returned by `cwac_scan`.                                |
| `audit_type` | `string` | No       | All types   | Filter by audit type (e.g., `"axe_core_audit"`, `"html_validation"`). |
| `impact`     | `string` | No       | All impacts | Filter by axe-core impact level: `"critical"`, `"serious"`, `"moderate"`, `"minor"`. |
| `limit`      | `integer`| No       | `100`       | Maximum number of result rows to return.                            |

### Return Value

```json
{
  "scan_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "audit_type": "axe_core_audit",
  "total_results": 47,
  "returned_results": 47,
  "results": [
    {
      "url": "https://example.com",
      "rule_id": "color-contrast",
      "impact": "serious",
      "description": "Elements must have sufficient color contrast",
      "html": "<p class=\"subtitle\" style=\"color: #999\">Welcome</p>",
      "target": ".subtitle",
      "help_url": "https://dequeuniversity.com/rules/axe/4.7/color-contrast"
    }
  ]
}
```

### Behaviour

1. **Look up scan.** Find the `ScanRecord` and verify status is `complete`.
2. **Locate results directory.** Identify the results directory from the scan record.
3. **List CSV files.** Find all `.csv` files in the results directory.
4. **Filter by audit type.** If `audit_type` is specified, select only the matching CSV file (e.g., `axe_core_audit.csv`).
5. **Read and parse CSVs.** Read each CSV using Python's `csv.DictReader`. Convert each row to a JSON object.
6. **Filter by impact.** If `impact` is specified, include only rows where the impact column matches.
7. **Apply limit.** Truncate the results to the specified limit.
8. **Return results array** with metadata.

### Error Conditions

| Condition                  | Response                                                    |
|----------------------------|-------------------------------------------------------------|
| Unknown `scan_id`          | Error: "No scan found with ID: {scan_id}"                   |
| Scan not complete          | Error: "Scan is still running. Check status first."          |
| No results directory       | Error: "Results directory not found for scan: {scan_id}"     |
| Unknown `audit_type`       | Error: "No results file for audit type: {audit_type}"        |

---

## Tool 4: `cwac_get_summary`

**Purpose:** Get an aggregated summary of scan findings.

### Description

Reads all result CSVs from a completed scan and produces an aggregated summary including issue counts by audit type, impact level, and top violations.

### Parameters

| Parameter  | Type     | Required | Description                      |
|------------|----------|----------|----------------------------------|
| `scan_id`  | `string` | Yes      | The scan ID returned by `cwac_scan`. |

### Return Value

```json
{
  "scan_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "audit_name": "scan_2026-02-24_14-30-00",
  "total_issues": 127,
  "issues_by_audit_type": {
    "axe_core_audit": 89,
    "html_validation": 38
  },
  "issues_by_impact": {
    "critical": 3,
    "serious": 24,
    "moderate": 41,
    "minor": 21,
    "unknown": 38
  },
  "top_violations": [
    {
      "rule_id": "color-contrast",
      "count": 18,
      "impact": "serious",
      "description": "Elements must have sufficient color contrast"
    },
    {
      "rule_id": "image-alt",
      "count": 12,
      "impact": "critical",
      "description": "Images must have alternate text"
    }
  ],
  "urls_scanned": 15,
  "scan_duration": "5m 42s"
}
```

### Behaviour

1. **Look up scan.** Find the `ScanRecord` and verify status is `complete`.
2. **Read all result CSVs.** Parse every CSV file in the results directory.
3. **Count by audit type.** Sum the number of rows in each CSV file.
4. **Count by impact.** For audit types that include an impact column (e.g., axe_core_audit), count rows by impact level. Rows without an impact value are counted as `"unknown"`.
5. **Identify top violations.** For axe_core_audit results, group by `rule_id`, count occurrences, and sort descending. Return the top 10.
6. **Count unique URLs.** Deduplicate the `url` column across all results.
7. **Calculate duration.** Use the scan record's `start_time` and `end_time`.
8. **Return summary object.**

### Error Conditions

| Condition                  | Response                                                    |
|----------------------------|-------------------------------------------------------------|
| Unknown `scan_id`          | Error: "No scan found with ID: {scan_id}"                   |
| Scan not complete          | Error: "Scan is still running. Check status first."          |
| No results found           | Returns summary with `total_issues: 0` and empty aggregations |

---

## Tool 5: `cwac_list_scans`

**Purpose:** List all available scan results.

### Description

Scans the CWAC results directory and returns metadata about each available scan. This includes scans initiated through the MCP server as well as scans run directly via the CWAC CLI.

### Parameters

This tool takes no parameters.

### Return Value

```json
{
  "scans": [
    {
      "name": "scan_2026-02-24_14-30-00_20260224_143542",
      "timestamp": "2026-02-24T14:35:42",
      "path": "/workspaces/cwac/results/scan_2026-02-24_14-30-00_20260224_143542/",
      "audit_types": ["axe_core_audit", "html_validation"],
      "file_count": 4,
      "size_bytes": 524288
    },
    {
      "name": "fincap_audit_20260220_091500",
      "timestamp": "2026-02-20T09:15:00",
      "path": "/workspaces/cwac/results/fincap_audit_20260220_091500/",
      "audit_types": ["axe_core_audit"],
      "file_count": 2,
      "size_bytes": 131072
    }
  ],
  "total_scans": 2,
  "results_directory": "/workspaces/cwac/results/"
}
```

### Behaviour

1. **List results directory.** Enumerate subdirectories in `/workspaces/cwac/results/`.
2. **For each subdirectory:**
   - Extract the directory name.
   - Parse the timestamp from the directory name (CWAC uses `{audit_name}_{YYYYMMDD}_{HHMMSS}` format).
   - List CSV files to determine audit types.
   - Calculate total file count and size.
3. **Sort by timestamp** descending (most recent first).
4. **Return scan list.**

### Error Conditions

| Condition                     | Response                                                |
|-------------------------------|---------------------------------------------------------|
| Results directory not found   | Returns `{"scans": [], "total_scans": 0}` with a note  |
| Directory read permission error | Error: "Cannot read results directory: {details}"     |

---

## Tool 6: `cwac_generate_report`

**Purpose:** Generate leaderboard reports from scan data.

### Description

Runs CWAC's `export_report_data.py` script to generate formatted reports from completed scan results. This produces the leaderboard-style reports that CWAC uses for organisational comparison.

### Parameters

| Parameter  | Type     | Required | Description                      |
|------------|----------|----------|----------------------------------|
| `scan_id`  | `string` | Yes      | The scan ID returned by `cwac_scan`. |

### Return Value

```json
{
  "scan_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "generated",
  "report_files": [
    "/workspaces/cwac/results/scan_2026-02-24_14-30-00_20260224_143542/report_data.json",
    "/workspaces/cwac/results/scan_2026-02-24_14-30-00_20260224_143542/leaderboard.csv"
  ]
}
```

### Behaviour

1. **Look up scan.** Find the `ScanRecord` and verify status is `complete`.
2. **Determine results directory** from the scan record.
3. **Launch report subprocess.** Execute:
   ```python
   subprocess.run(
       ["python", "export_report_data.py", results_dir],
       cwd="/workspaces/cwac",
       capture_output=True,
       text=True,
       timeout=120
   )
   ```
4. **Verify output files.** Check that expected report files were created in the results directory.
5. **Return file paths** of generated reports.

### Error Conditions

| Condition                    | Response                                                    |
|------------------------------|-------------------------------------------------------------|
| Unknown `scan_id`            | Error: "No scan found with ID: {scan_id}"                   |
| Scan not complete            | Error: "Scan is still running. Check status first."          |
| Report script not found      | Error: "export_report_data.py not found in CWAC directory"   |
| Report generation failed     | Error: "Report generation failed: {stderr}"                  |
| Timeout                      | Error: "Report generation timed out after 120 seconds"       |

---

## Tool Registration

All tools are registered at server startup using the MCP SDK's tool registration mechanism. Example registration pattern:

```python
@server.tool()
async def cwac_scan(
    urls: list[str],
    audit_name: str | None = None,
    plugins: dict[str, bool] | None = None,
    max_links_per_domain: int = 50,
    viewport_sizes: dict | None = None,
) -> dict:
    """Start a CWAC accessibility scan against one or more URLs."""
    ...
```

The MCP framework automatically generates JSON schemas from the Python type annotations and docstrings, making the tools discoverable by Claude Code.

---

## Related Specifications

| Spec ID    | Relationship | Title                      |
|------------|-------------|----------------------------|
| SPEC-002-A | Implements  | Subprocess Execution Model |
| SPEC-003-A | Implements  | Scan Registry Design       |

## Changelog

| Version | Date       | Author        | Changes                          |
|---------|------------|---------------|----------------------------------|
| A       | 2026-02-24 | Chris Barlow  | Initial specification            |
