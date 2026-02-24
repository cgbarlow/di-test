# SPEC-003-A: Scan Registry Design

| Field           | Value                                        |
|-----------------|----------------------------------------------|
| **Parent ADR**  | ADR-003 (Scan Lifecycle Management)          |
| **Version**     | A (initial)                                  |
| **Status**      | Draft                                        |
| **Date**        | 2026-02-24                                   |

## Overview

This specification defines the scan registry: the in-memory data structure that tracks all CWAC scans initiated through the MCP server. The registry maps scan IDs to scan records, enabling the MCP tools to manage scan lifecycles, monitor progress, and retrieve results across multiple tool invocations.

---

## 1. Registry Data Structure

### Top-level Registry

The registry is a module-level dictionary:

```python
from typing import Dict

scans: Dict[str, ScanRecord] = {}
```

The dictionary maps scan IDs (strings) to `ScanRecord` instances. It is the single source of truth for all scan state within the MCP server process.

### ScanRecord Definition

```python
from dataclasses import dataclass, field
from datetime import datetime
from subprocess import Popen
from typing import Optional
from enum import Enum


class ScanStatus(Enum):
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class ScanRecord:
    """Tracks the state of a single CWAC scan."""

    # Process management
    process: Popen
    """Handle to the CWAC subprocess. Used for polling and termination."""

    # File paths
    config_path: str
    """Absolute path to the generated config file.
    Example: /workspaces/cwac/config/mcp_a1b2c3d4.json"""

    base_urls_dir: str
    """Absolute path to the generated base URLs directory.
    Example: /workspaces/cwac/base_urls/visit/mcp_a1b2c3d4/"""

    results_dir: Optional[str] = None
    """Absolute path to the results directory created by CWAC.
    None until the scan completes and the directory is located.
    Example: /workspaces/cwac/results/scan_2026-02-24_20260224_143542/"""

    # Status tracking
    status: ScanStatus = ScanStatus.RUNNING
    """Current scan state. Transitions: RUNNING -> COMPLETE or RUNNING -> FAILED."""

    start_time: datetime = field(default_factory=datetime.now)
    """When the scan was initiated (subprocess launched)."""

    end_time: Optional[datetime] = None
    """When the scan completed or failed. None while running."""

    # Metadata
    audit_name: str = ""
    """Human-readable name for the scan. Used to locate the results directory."""

    # Output capture
    stdout: str = ""
    """Accumulated stdout from the subprocess. Appended incrementally during status checks."""

    stderr: str = ""
    """Captured stderr from the subprocess. Populated when the scan fails."""
```

### Field Details

| Field          | Type                 | Initial Value          | Mutability | Description                                                                                         |
|----------------|----------------------|------------------------|------------|-----------------------------------------------------------------------------------------------------|
| `process`      | `Popen`              | Set at creation        | Read-only  | The subprocess handle. Never reassigned after creation.                                              |
| `config_path`  | `str`                | Set at creation        | Read-only  | Path to the temp config file. Used for cleanup.                                                      |
| `base_urls_dir`| `str`                | Set at creation        | Read-only  | Path to the temp base URLs directory. Used for cleanup.                                              |
| `results_dir`  | `str` or `None`      | `None`                 | Set once   | Discovered after scan completion. Set once, never changed.                                           |
| `status`       | `ScanStatus`         | `RUNNING`              | Updated    | Transitions only forward: `RUNNING` to `COMPLETE` or `FAILED`.                                       |
| `start_time`   | `datetime`           | `datetime.now()`       | Read-only  | Recorded at subprocess launch time.                                                                  |
| `end_time`     | `datetime` or `None` | `None`                 | Set once   | Set when status transitions to `COMPLETE` or `FAILED`.                                               |
| `audit_name`   | `str`                | Set at creation        | Read-only  | Derived from the `audit_name` parameter or auto-generated.                                           |
| `stdout`       | `str`                | `""`                   | Appended   | Grows incrementally as stdout is read during status checks.                                          |
| `stderr`       | `str`                | `""`                   | Set once   | Populated from the subprocess stderr pipe when the scan fails.                                       |

---

## 2. Scan ID Generation

### Format

Scan IDs are generated using UUID4:

```python
import uuid

scan_id = str(uuid.uuid4())
# Example: "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
```

### Properties

| Property      | Value                                                                 |
|---------------|-----------------------------------------------------------------------|
| Format        | UUID4 string (36 characters including hyphens)                        |
| Uniqueness    | Globally unique with negligible collision probability                 |
| Ordering      | Not sequential; cannot be used to determine scan order                |
| Persistence   | Exists only in memory; not stored on disk                             |
| Derivation    | Used to generate file paths: `mcp_{scan_id[:8]}` for brevity         |

### Short Form for File Names

Config files and base URL directories use a truncated form of the scan ID for readability:

```python
short_id = scan_id[:8]  # "a1b2c3d4"
config_filename = f"mcp_{short_id}.json"
base_urls_dirname = f"mcp_{short_id}"
```

The full UUID is retained in the registry as the lookup key. The short form is used only for file system paths where a shorter name is more practical.

---

## 3. Status Transitions

### State Machine

```
             +---------+
  Creation   | RUNNING |
  ---------> |         |
             +----+----+
                  |
       +----------+----------+
       |                     |
  poll() == 0           poll() != 0
       |                     |
  +----v------+        +-----v----+
  | COMPLETE  |        |  FAILED  |
  |           |        |          |
  +-----------+        +----------+
```

### Transition Rules

| From      | To        | Trigger                        | Side Effects                                                  |
|-----------|-----------|--------------------------------|---------------------------------------------------------------|
| `RUNNING` | `COMPLETE`| `process.poll()` returns `0`   | Set `end_time`, discover `results_dir`, trigger cleanup       |
| `RUNNING` | `FAILED`  | `process.poll()` returns non-zero | Set `end_time`, capture `stderr`, trigger cleanup          |

### Transition Enforcement

- Status can only move forward. There is no mechanism to reset a completed or failed scan to running.
- The `RUNNING` to `COMPLETE`/`FAILED` transition occurs exactly once, when `cwac_scan_status` detects process termination.
- Multiple calls to `cwac_scan_status` after the transition return the same final status without side effects.

### Transition Implementation

```python
def update_scan_status(scan_record: ScanRecord) -> None:
    """Check subprocess state and update scan record if needed."""
    if scan_record.status != ScanStatus.RUNNING:
        return  # Already in terminal state

    return_code = scan_record.process.poll()

    if return_code is None:
        # Still running - read available stdout
        new_output = read_available_output(scan_record.process.stdout)
        scan_record.stdout += new_output
        return

    # Process has exited
    scan_record.end_time = datetime.now()

    if return_code == 0:
        scan_record.status = ScanStatus.COMPLETE
        scan_record.stdout += scan_record.process.stdout.read()
        scan_record.results_dir = find_results_dir(scan_record)
    else:
        scan_record.status = ScanStatus.FAILED
        scan_record.stdout += scan_record.process.stdout.read()
        scan_record.stderr = scan_record.process.stderr.read()

    trigger_cleanup(scan_record)
```

---

## 4. Cleanup Behaviour

### Temporary Files

When a scan transitions to a terminal state (`COMPLETE` or `FAILED`), the following temporary files are removed:

| File/Directory                                    | Created By    | Purpose                        |
|---------------------------------------------------|---------------|--------------------------------|
| `/workspaces/cwac/config/mcp_{short_id}.json`     | MCP server    | Scan-specific config           |
| `/workspaces/cwac/base_urls/visit/mcp_{short_id}/`| MCP server    | Scan-specific URL inputs       |

### Preserved Files

The results directory created by CWAC is preserved indefinitely. It is the responsibility of the user (or a future cleanup tool) to manage results storage.

### Cleanup Failure Handling

If cleanup fails (e.g., file already deleted, permission error), the error is logged but does not affect the scan record's status or the tool's return value. Cleanup failures are non-fatal.

```python
def trigger_cleanup(scan_record: ScanRecord) -> None:
    """Remove temporary files. Errors are logged but not raised."""
    try:
        if os.path.exists(scan_record.config_path):
            os.remove(scan_record.config_path)
    except OSError as e:
        logger.warning(f"Failed to remove config: {e}")

    try:
        if os.path.exists(scan_record.base_urls_dir):
            shutil.rmtree(scan_record.base_urls_dir)
    except OSError as e:
        logger.warning(f"Failed to remove base_urls dir: {e}")
```

### Server Shutdown Cleanup

On server shutdown, all running processes are terminated and all temporary files are cleaned:

```python
def shutdown_cleanup() -> None:
    """Terminate running scans and clean up temp files on server exit."""
    for scan_id, record in scans.items():
        if record.status == ScanStatus.RUNNING:
            record.process.terminate()
            try:
                record.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                record.process.kill()
        trigger_cleanup(record)
```

---

## 5. Thread Safety Considerations

### Current Design: Single-threaded

The MCP server processes tool calls sequentially (one at a time). In this mode, the registry requires no synchronisation because:

- Only one tool handler executes at a time.
- Status updates and registry reads/writes are atomic from the application's perspective.
- The `Popen.poll()` method is safe to call from any thread.

### Future: Concurrent Tool Handling

If the MCP server is extended to handle tool calls concurrently (e.g., using `asyncio` tasks or threading), the following considerations apply:

| Concern                     | Risk                                              | Mitigation                                          |
|-----------------------------|---------------------------------------------------|-----------------------------------------------------|
| Registry reads during writes | `cwac_scan` adds a record while `cwac_scan_status` iterates | Use `threading.Lock` around registry access          |
| Duplicate status transitions | Two concurrent `cwac_scan_status` calls detect completion simultaneously | Guard transition with a status check before update   |
| stdout accumulation         | Two threads read from the same stdout pipe        | Ensure only one reader per pipe; use a lock          |
| Cleanup race conditions     | Cleanup triggered twice for the same scan         | Use `os.path.exists` check before deletion (idempotent) |

Recommended locking pattern for future concurrent use:

```python
import threading

registry_lock = threading.Lock()

def get_scan(scan_id: str) -> Optional[ScanRecord]:
    with registry_lock:
        return scans.get(scan_id)

def register_scan(scan_id: str, record: ScanRecord) -> None:
    with registry_lock:
        scans[scan_id] = record
```

---

## 6. Limitations

### In-memory Only

The scan registry exists solely in the MCP server's process memory. This has the following implications:

| Scenario                          | Consequence                                                          |
|-----------------------------------|----------------------------------------------------------------------|
| Server restart                    | All scan records are lost. Running subprocesses become orphaned.     |
| Server crash                      | Same as restart, plus temp files may not be cleaned up.              |
| Multiple server instances         | Each instance has its own isolated registry. No shared state.        |
| Long-running server               | Completed scan records accumulate in memory indefinitely.            |

### No Persistence Across Restarts

When the server restarts:

- Active scans are lost. The subprocess may still be running (if the OS did not kill it), but the MCP server has no way to reconnect to it.
- The `cwac_list_scans` tool can still discover completed scan results on disk, but they are not associated with scan IDs.
- Users must initiate a new scan if the server restarts during an active scan.

### Orphaned Process Detection

The current design does not detect or recover orphaned processes (CWAC subprocesses still running after a server restart). A future enhancement could:

1. Write the PID of each subprocess to a file (e.g., `/workspaces/cwac/.mcp_pids`).
2. On server startup, check for running processes matching those PIDs.
3. Either reconnect to the process or terminate it.

### Memory Growth

Each `ScanRecord` is small (a few kilobytes for the subprocess handle and captured output). However, the `stdout` field grows with the length of the CWAC output. For very long scans producing verbose output, this could become significant.

Potential mitigations:

- Cap `stdout` at a maximum length (e.g., 1 MB), retaining only the most recent output.
- Periodically flush accumulated `stdout` to a file and clear the in-memory buffer.
- Automatically remove scan records older than a configurable threshold.

---

## 7. Registry Operations Summary

| Operation       | Tool                | Registry Action                          |
|-----------------|---------------------|------------------------------------------|
| Create scan     | `cwac_scan`         | `scans[scan_id] = ScanRecord(...)`       |
| Check status    | `cwac_scan_status`  | `update_scan_status(scans[scan_id])`     |
| Get results     | `cwac_get_results`  | `scans[scan_id].results_dir` (read-only) |
| Get summary     | `cwac_get_summary`  | `scans[scan_id].results_dir` (read-only) |
| List scans      | `cwac_list_scans`   | No registry access (reads filesystem)    |
| Generate report | `cwac_generate_report` | `scans[scan_id].results_dir` (read-only) |

---

## Related Specifications

| Spec ID    | Relationship  | Title                      |
|------------|--------------|----------------------------|
| SPEC-001-A | Specified by | MCP Tool Definitions       |
| SPEC-002-A | Relates to   | Subprocess Execution Model |

## Changelog

| Version | Date       | Author        | Changes                          |
|---------|------------|---------------|----------------------------------|
| A       | 2026-02-24 | Chris Barlow  | Initial specification            |
