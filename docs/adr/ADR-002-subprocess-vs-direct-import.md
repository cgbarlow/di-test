# ADR-002: Subprocess vs Direct Import

| Field    | Value                                        |
|----------|----------------------------------------------|
| **ID**   | ADR-002                                      |
| **Status** | Accepted                                   |
| **Date** | 2026-02-24                                   |
| **Author** | Chris Barlow                               |

## WH(Y) Decision Statement

**In the context of** integrating CWAC's Python codebase into the MCP server,

**facing** CWAC's pervasive use of relative paths (`./config/`, `./base_urls/`, `./results/`), global state (`AuditManager.axe_core_js`), and tight coupling to its working directory,

**we decided for** a subprocess wrapper that runs CWAC in its own directory with generated config files,

**and neglected** direct Python import with path patching, and forking CWAC to refactor paths,

**to achieve** zero modification to CWAC source, clean separation of concerns, and compatibility with CWAC updates,

**accepting that** there is subprocess overhead, IPC complexity for status monitoring, and temp file management.

## Context

CWAC is a standalone Python application designed to be run from its own directory. Its codebase makes extensive assumptions about the working directory, using relative paths throughout for configuration, input data, and output results. Understanding these constraints is essential for choosing the right integration strategy.

### CWAC's Technical Constraints

**1. Relative path dependencies**

CWAC's `config.py` module reads configuration files from `./config/`. The default configuration file is `./config/config_default.json`. When a scan is initiated, CWAC reads the config file path relative to its own directory:

```python
# In CWAC's config.py
config_path = f"./config/{config_filename}"
with open(config_path) as f:
    config = json.load(f)
```

**2. Base URLs directory structure**

CWAC reads target URLs from CSV files located in `./base_urls/visit/`. The config file specifies a `base_urls_visit_path` value such as `./base_urls/visit/my_scan/`, and CWAC iterates over all `.csv` files in that directory. Each CSV must have an `organisation,url,sector` header row.

**3. Results output directory**

Scan results are written to `./results/` in a timestamped subdirectory. CWAC creates this directory structure automatically and writes CSV files for each audit type (e.g., `axe_core_audit.csv`, `html_validation.csv`). The results path is not configurable; it is derived from the audit name and timestamp.

**4. Global state and singleton patterns**

`AuditManager` loads `axe_core_js` (the axe-core JavaScript bundle) as a class-level attribute on first use. This global state assumes a single CWAC instance per process. Other modules maintain state through module-level variables and file handles.

**5. Working directory assumption**

The `cwac.py` entry point expects to be invoked from the CWAC root directory. Internal imports, resource loading, and all file I/O assume `os.getcwd()` returns the CWAC installation directory.

## Decision

The MCP server will invoke CWAC as a **subprocess** using `subprocess.Popen`, with the working directory set to the CWAC installation path:

```python
process = subprocess.Popen(
    ["python", "cwac.py", config_filename],
    cwd="/workspaces/cwac",
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)
```

The MCP server generates configuration and input files in the locations CWAC expects, launches CWAC as an independent process, and reads the resulting output files after the scan completes.

## Alternatives Considered

### Alternative 1: Direct Python import with path patching

This approach would add CWAC's directory to `sys.path` and import its modules directly:

```python
import sys
sys.path.insert(0, "/workspaces/cwac")
from cwac import run_audit
```

**Why it was rejected:**

- CWAC's relative path usage means `os.chdir("/workspaces/cwac")` would be required before any CWAC code executes. `os.chdir` affects the entire process and is not thread-safe, making concurrent scans impossible.
- Global state in `AuditManager` and other modules would leak between scans. There is no clean way to reset CWAC's internal state between invocations without restarting the process.
- Any Python module that CWAC imports could have side effects at import time (module-level file reads, global variable initialisation). These side effects would occur in the MCP server's process context, potentially corrupting the server's own state.
- Errors in CWAC code (uncaught exceptions, `sys.exit()` calls) would crash the MCP server process.

### Alternative 2: Forking CWAC to refactor paths

This approach would fork the CWAC repository and refactor all relative paths to accept configurable base directories:

**Why it was rejected:**

- Maintaining a fork creates an ongoing maintenance burden. Every upstream CWAC update would need to be merged, with potential conflicts in the refactored path handling code.
- CWAC is maintained by GOVTNZ and may receive updates for new audit types, bug fixes, or WCAG guideline changes. A fork risks falling behind on these improvements.
- The refactoring itself is non-trivial. Relative paths are used in `config.py`, `audit_manager.py`, `cwac.py`, and potentially in audit plugins. Each would need to be updated and tested.
- This approach modifies code we do not own, which raises concerns about licensing, attribution, and divergence from the official tool.

### Alternative 3: Docker container isolation

Wrapping CWAC in a Docker container was briefly considered:

**Why it was rejected:**

- Adds significant complexity (Dockerfile, container management, volume mounts) for a problem that subprocess isolation solves adequately.
- Increases startup time for each scan.
- Complicates development and debugging workflows.
- Not justified given that CWAC and the MCP server run on the same host.

## How the Subprocess Model Works

### Config file generation

When `cwac_scan` is called, the MCP server:

1. Reads CWAC's default config (`/workspaces/cwac/config/config_default.json`).
2. Overrides fields based on tool parameters (plugins, max_links, viewport sizes).
3. Writes the modified config to `/workspaces/cwac/config/mcp_{scan_id}.json`.

### Base URLs CSV generation

1. Creates the directory `/workspaces/cwac/base_urls/visit/mcp_{scan_id}/`.
2. Writes a `urls.csv` file with the `organisation,url,sector` header.
3. Sets `base_urls_visit_path` in the config to `./base_urls/visit/mcp_{scan_id}/`.

### Process monitoring

The MCP server retains a reference to the `Popen` object. The `cwac_scan_status` tool calls `process.poll()` to check whether the process is still running, and reads from `stdout`/`stderr` pipes for progress information.

### Cleanup

After a scan completes (or fails), the MCP server removes the temporary config file and base URLs directory. The results directory is preserved for retrieval.

## Consequences

### Positive

- **Zero CWAC modifications.** CWAC is used exactly as its developers intended. No patches, no forks, no monkey-patching.
- **Process isolation.** CWAC crashes, memory leaks, or unexpected behaviour cannot affect the MCP server. Each scan runs in its own process with its own memory space.
- **Concurrency support.** Multiple scans can run simultaneously since each is an independent process with its own config file and working directory context.
- **Update compatibility.** CWAC can be updated by pulling the latest code. As long as the CLI interface (`python cwac.py <config>`) and output format (CSV files in `./results/`) remain stable, the MCP server requires no changes.
- **Debuggability.** The generated config files and base URL CSVs can be inspected directly. The same subprocess command can be run manually for debugging.

### Negative

- **Subprocess overhead.** Each scan launches a new Python interpreter, which has startup costs. For small scans this overhead is noticeable relative to the scan time.
- **IPC complexity.** Monitoring scan progress requires polling the subprocess and reading from pipes. There is no structured progress API; the MCP server must parse CWAC's stdout for status information.
- **Temp file management.** The MCP server must create and clean up config files and base URL directories. Incomplete cleanup (e.g., server crash during a scan) can leave orphaned files.
- **No streaming results.** Results are only available after CWAC writes them to disk. There is no way to stream partial results during a long-running scan.

## Dependencies

| Relationship  | Target   | Description                                            |
|---------------|----------|--------------------------------------------------------|
| DEPENDS_ON    | ADR-001  | This decision implements the integration approach      |
| RELATES_TO    | ADR-003  | Scan lifecycle management depends on subprocess model  |

## Referenced Specification

| Spec ID    | Title                      | Version |
|------------|----------------------------|---------|
| SPEC-002-A | Subprocess Execution Model | A       |

## Status History

| Date       | Status   | Changed By    | Notes                     |
|------------|----------|---------------|---------------------------|
| 2026-02-24 | Accepted | Chris Barlow  | Initial decision recorded |

## Governance

This ADR was authored following the WH(Y) decision format from [cgbarlow/adr](https://github.com/cgbarlow/adr). Changes to this decision require a new ADR that supersedes this one.
