# SPEC-002-A: Subprocess Execution Model

| Field           | Value                                        |
|-----------------|----------------------------------------------|
| **Parent ADR**  | ADR-002 (Subprocess vs Direct Import)        |
| **Version**     | A (initial)                                  |
| **Status**      | Draft                                        |
| **Date**        | 2026-02-24                                   |

## Overview

This specification details how the CWAC MCP Server invokes CWAC as a subprocess, including configuration file generation, base URLs CSV creation, process launching, monitoring, and cleanup. The subprocess model provides complete isolation between the MCP server and CWAC, allowing CWAC to run unmodified in its expected directory context.

---

## 1. CWAC Invocation

### Command

CWAC is invoked using Python's `subprocess.Popen`:

```python
import subprocess

process = subprocess.Popen(
    ["python", "cwac.py", config_filename],
    cwd="/workspaces/cwac",
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1  # Line-buffered for real-time stdout reading
)
```

### Parameters

| Parameter        | Value                                    | Rationale                                              |
|------------------|------------------------------------------|--------------------------------------------------------|
| `args`           | `["python", "cwac.py", config_filename]` | Matches CWAC's expected invocation pattern              |
| `cwd`            | `"/workspaces/cwac"`                     | CWAC requires running from its own directory            |
| `stdout`         | `subprocess.PIPE`                        | Capture output for status monitoring                   |
| `stderr`         | `subprocess.PIPE`                        | Capture errors for failure diagnosis                   |
| `text`           | `True`                                   | Decode output as UTF-8 strings                         |
| `bufsize`        | `1`                                      | Line-buffered to allow incremental stdout reading      |

### Working Directory

The `cwd="/workspaces/cwac"` parameter is critical. CWAC's entire codebase assumes the working directory is its own installation root. Without this:

- `config.py` would fail to find `./config/config_default.json`
- Base URLs would not be found in `./base_urls/visit/`
- Results would be written to the wrong location
- Internal imports might fail if CWAC uses relative module paths

---

## 2. Configuration File Generation

### Source

The MCP server uses CWAC's own default configuration as a starting point:

```
/workspaces/cwac/config/config_default.json
```

This file is read, parsed as JSON, modified with scan-specific overrides, and written to a new location.

### Generated Config Path

```
/workspaces/cwac/config/mcp_{scan_id}.json
```

The `mcp_` prefix distinguishes MCP-generated configs from manually created ones, preventing naming collisions.

### Config Override Process

```python
import json
import uuid

scan_id = str(uuid.uuid4())[:8]  # Short form for filename readability

# 1. Load default config
with open("/workspaces/cwac/config/config_default.json") as f:
    config = json.load(f)

# 2. Override base_urls_visit_path
config["base_urls_visit_path"] = f"./base_urls/visit/mcp_{scan_id}/"

# 3. Override audit name
config["audit_name"] = audit_name or f"scan_{timestamp}"

# 4. Override plugins if specified
if plugins:
    for plugin_name, enabled in plugins.items():
        if plugin_name in config.get("plugins", {}):
            config["plugins"][plugin_name] = enabled

# 5. Override max_links_per_domain if specified
if max_links_per_domain is not None:
    config["max_links_per_domain"] = max_links_per_domain

# 6. Override viewport sizes if specified
if viewport_sizes:
    config["viewport_width"] = viewport_sizes.get("width", config.get("viewport_width"))
    config["viewport_height"] = viewport_sizes.get("height", config.get("viewport_height"))

# 7. Write config
config_filename = f"mcp_{scan_id}.json"
config_path = f"/workspaces/cwac/config/{config_filename}"
with open(config_path, "w") as f:
    json.dump(config, f, indent=2)
```

### Config Fields Modified

| Field                    | Source                    | Description                                  |
|--------------------------|---------------------------|----------------------------------------------|
| `base_urls_visit_path`   | Always set by MCP server  | Points to the generated base URLs directory  |
| `audit_name`             | `audit_name` parameter    | Human-readable scan name                     |
| `plugins`                | `plugins` parameter       | Enable/disable specific audit plugins        |
| `max_links_per_domain`   | `max_links_per_domain` parameter | Limit crawl depth                     |
| `viewport_width`         | `viewport_sizes` parameter | Browser viewport width                      |
| `viewport_height`        | `viewport_sizes` parameter | Browser viewport height                     |

All other config fields retain their default values from `config_default.json`.

---

## 3. Base URLs CSV Generation

### Directory Structure

CWAC expects base URLs to be in a specific directory structure:

```
/workspaces/cwac/base_urls/visit/mcp_{scan_id}/
    urls.csv
```

The `base_urls_visit_path` config field points to this directory. CWAC reads all `.csv` files found in the directory.

### CSV Format

The CSV file must have the header `organisation,url,sector`:

```csv
organisation,url,sector
example.com,https://example.com,unknown
example.com,https://example.com/about,unknown
other-site.org,https://other-site.org,unknown
```

### Generation Process

```python
import os
import csv
from urllib.parse import urlparse

base_urls_dir = f"/workspaces/cwac/base_urls/visit/mcp_{scan_id}/"
os.makedirs(base_urls_dir, exist_ok=True)

csv_path = os.path.join(base_urls_dir, "urls.csv")
with open(csv_path, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["organisation", "url", "sector"])
    for url in urls:
        parsed = urlparse(url)
        organisation = parsed.netloc  # e.g., "example.com"
        writer.writerow([organisation, url, "unknown"])
```

### Field Mapping

| CSV Column      | Source                  | Description                                       |
|-----------------|-------------------------|---------------------------------------------------|
| `organisation`  | Derived from URL domain | Used by CWAC for grouping and reporting            |
| `url`           | `urls` parameter        | The target URL to scan                             |
| `sector`        | Default: `"unknown"`    | Used by CWAC's leaderboard reporting               |

---

## 4. Process Monitoring

### Poll-based Status Checking

The MCP server uses `process.poll()` to check subprocess state:

```python
def check_scan_status(scan_record):
    return_code = scan_record.process.poll()

    if return_code is None:
        # Still running
        scan_record.status = "running"
        # Read available stdout without blocking
        stdout_lines = read_available_output(scan_record.process.stdout)
        scan_record.stdout += stdout_lines
        return {
            "status": "running",
            "elapsed_time": format_elapsed(scan_record.start_time),
            "stdout_tail": get_last_n_lines(scan_record.stdout, 20)
        }

    elif return_code == 0:
        # Completed successfully
        scan_record.status = "complete"
        scan_record.end_time = datetime.now()
        scan_record.stdout += scan_record.process.stdout.read()
        trigger_cleanup(scan_record)
        return {
            "status": "complete",
            "elapsed_time": format_elapsed(scan_record.start_time, scan_record.end_time),
            "results_dir": find_results_dir(scan_record),
            "exit_code": 0
        }

    else:
        # Failed
        scan_record.status = "failed"
        scan_record.end_time = datetime.now()
        scan_record.stderr = scan_record.process.stderr.read()
        trigger_cleanup(scan_record)
        return {
            "status": "failed",
            "elapsed_time": format_elapsed(scan_record.start_time, scan_record.end_time),
            "exit_code": return_code,
            "stderr": scan_record.stderr
        }
```

### Non-blocking stdout Reading

Reading from `stdout` must not block, as the subprocess may still be running and producing output intermittently:

```python
import select
import os

def read_available_output(pipe):
    """Read whatever is available from the pipe without blocking."""
    output = ""
    fd = pipe.fileno()
    while select.select([fd], [], [], 0)[0]:
        chunk = os.read(fd, 4096)
        if not chunk:
            break
        output += chunk.decode("utf-8", errors="replace")
    return output
```

### Results Directory Discovery

CWAC creates a results directory with a timestamped name. The MCP server must locate this directory after the scan completes:

```python
import os
import glob

def find_results_dir(scan_record):
    """Find the results directory created by CWAC for this scan."""
    audit_name = scan_record.audit_name
    results_base = "/workspaces/cwac/results/"

    # CWAC creates directories as: {audit_name}_{YYYYMMDD}_{HHMMSS}
    pattern = os.path.join(results_base, f"{audit_name}_*")
    matches = sorted(glob.glob(pattern), reverse=True)

    if matches:
        scan_record.results_dir = matches[0]
        return matches[0]

    return None
```

---

## 5. Cleanup

### What Gets Cleaned Up

After a scan completes (success or failure), the following temporary files are removed:

| Item                                              | Type      | When Removed           |
|---------------------------------------------------|-----------|------------------------|
| `/workspaces/cwac/config/mcp_{scan_id}.json`      | File      | After scan completes   |
| `/workspaces/cwac/base_urls/visit/mcp_{scan_id}/` | Directory | After scan completes   |

### What Is Preserved

| Item                                                              | Type      | Reason                          |
|-------------------------------------------------------------------|-----------|---------------------------------|
| `/workspaces/cwac/results/{audit_name}_{timestamp}/`              | Directory | Contains scan results for retrieval |

### Cleanup Implementation

```python
import os
import shutil

def trigger_cleanup(scan_record):
    """Remove temporary config and base URLs files."""
    # Remove config file
    if os.path.exists(scan_record.config_path):
        os.remove(scan_record.config_path)

    # Remove base URLs directory
    if os.path.exists(scan_record.base_urls_dir):
        shutil.rmtree(scan_record.base_urls_dir)
```

### Cleanup Timing

Cleanup is triggered when `cwac_scan_status` detects that the subprocess has exited. This means:

- If `cwac_scan_status` is never called, cleanup does not occur until the server shuts down.
- The server should also perform cleanup during its shutdown sequence for any remaining temp files.
- A periodic cleanup task (e.g., every 5 minutes) could be added to handle scans that complete without a status check.

---

## 6. Error Handling

### Subprocess Failure to Start

If `Popen` raises an exception (e.g., `FileNotFoundError` because Python is not installed, or `PermissionError`), the error is caught and returned to the MCP client:

```python
try:
    process = subprocess.Popen(...)
except FileNotFoundError:
    return {"error": "Python interpreter not found. Is Python installed?"}
except PermissionError:
    return {"error": "Permission denied when running CWAC"}
except Exception as e:
    return {"error": f"Failed to start CWAC process: {str(e)}"}
```

### Timeout Handling

CWAC scans do not have a built-in timeout. The MCP server does not enforce a timeout by default, but provides the infrastructure to do so:

```python
import signal

def kill_scan(scan_id, timeout_seconds=3600):
    """Kill a scan that has exceeded the timeout."""
    scan_record = scans.get(scan_id)
    if scan_record and scan_record.status == "running":
        elapsed = (datetime.now() - scan_record.start_time).total_seconds()
        if elapsed > timeout_seconds:
            scan_record.process.terminate()
            # Give 10 seconds for graceful shutdown
            try:
                scan_record.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                scan_record.process.kill()
            scan_record.status = "failed"
            scan_record.stderr = f"Scan killed after {timeout_seconds}s timeout"
            trigger_cleanup(scan_record)
```

### Process Kill on Server Shutdown

When the MCP server shuts down, all running subprocesses should be terminated:

```python
import atexit

def cleanup_all_scans():
    """Terminate all running scans on server shutdown."""
    for scan_id, record in scans.items():
        if record.status == "running":
            record.process.terminate()
            try:
                record.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                record.process.kill()
    # Clean up any remaining temp files
    for scan_id, record in scans.items():
        trigger_cleanup(record)

atexit.register(cleanup_all_scans)
```

### stderr Capture

CWAC's stderr output is captured for diagnostic purposes. When a scan fails, the full stderr content is stored in the scan record and returned by `cwac_scan_status`:

```python
# After process exits with non-zero code
scan_record.stderr = scan_record.process.stderr.read()
```

Common CWAC errors and their causes:

| stderr Pattern                           | Likely Cause                                    |
|------------------------------------------|-------------------------------------------------|
| `FileNotFoundError: chromedriver`        | Chrome/Chromedriver not installed                |
| `selenium.common.exceptions`             | Browser automation failure                       |
| `json.decoder.JSONDecodeError`           | Malformed config file                            |
| `FileNotFoundError: base_urls`           | Base URLs directory or CSV missing               |
| `ConnectionError`                        | Target URL unreachable                           |

---

## 7. File System Layout

The complete file system layout for a single MCP-initiated scan:

```
/workspaces/cwac/
    config/
        config_default.json          # CWAC's default (read-only)
        mcp_a1b2c3d4.json           # Generated config (temporary)
    base_urls/
        visit/
            mcp_a1b2c3d4/           # Generated directory (temporary)
                urls.csv             # Generated URLs (temporary)
    results/
        scan_2026-02-24_14-30-00_20260224_143542/   # Created by CWAC (preserved)
            axe_core_audit.csv
            html_validation.csv
            crawl_audit.csv
            seo_audit.csv
    cwac.py                          # CWAC entry point (unmodified)
    config.py                        # CWAC config module (unmodified)
    export_report_data.py            # CWAC reporting (unmodified)
```

Items marked **(temporary)** are created before the scan and removed after completion. Items marked **(preserved)** are created by CWAC during the scan and retained for result retrieval.

---

## Related Specifications

| Spec ID    | Relationship  | Title                |
|------------|--------------|----------------------|
| SPEC-001-A | Specified by | MCP Tool Definitions |
| SPEC-003-A | Relates to   | Scan Registry Design |

## Changelog

| Version | Date       | Author        | Changes                          |
|---------|------------|---------------|----------------------------------|
| A       | 2026-02-24 | Chris Barlow  | Initial specification            |
