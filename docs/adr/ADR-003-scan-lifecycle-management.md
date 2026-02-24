# ADR-003: Scan Lifecycle Management

| Field    | Value                                        |
|----------|----------------------------------------------|
| **ID**   | ADR-003                                      |
| **Status** | Accepted                                   |
| **Date** | 2026-02-24                                   |
| **Author** | Chris Barlow                               |

## WH(Y) Decision Statement

**In the context of** managing potentially long-running CWAC scans (minutes to hours for large sites),

**facing** the need for non-blocking scan initiation, progress tracking, and result retrieval,

**we decided for** an async scan model with a scan registry tracking process state and results paths,

**and neglected** synchronous blocking scans and external job queue systems,

**to achieve** responsive MCP interactions, concurrent scan support, and simple state management,

**accepting that** scan state is in-memory only (lost on server restart) and concurrent scans share CWAC resources.

## Context

CWAC scans are inherently long-running operations. A scan of a single page with all audit plugins enabled can take 30 seconds to several minutes. Scans that follow links across an entire domain (controlled by `max_links_per_domain`) can run for tens of minutes or even hours. Multi-domain scans multiply this further.

MCP tool calls are designed to return relatively quickly. While there is no strict timeout in the protocol, keeping a tool call open for minutes or hours is impractical:

- The user receives no feedback while a blocking tool call is in progress.
- Claude Code cannot perform other work while waiting for a tool response.
- Network interruptions or client restarts during a long-running call would lose all progress.
- There is no mechanism in MCP for streaming partial results from a single tool invocation.

The scan lifecycle must therefore be **asynchronous**: the scan is started by one tool call, monitored by subsequent calls, and results are retrieved by yet another call after the scan completes.

## Decision

We will implement an **async scan model** with an **in-memory scan registry** that tracks the state of all scans initiated through the MCP server.

### Scan Lifecycle

Every scan progresses through a defined set of states:

```
                    +-----------+
   cwac_scan -----> |  running  |
                    +-----+-----+
                          |
              +-----------+-----------+
              |                       |
        poll() == 0             poll() != 0
              |                       |
        +-----v-----+         +------v----+
        |  complete  |         |  failed   |
        +-----------+          +-----------+
```

**States:**

| State      | Description                                                  |
|------------|--------------------------------------------------------------|
| `running`  | CWAC subprocess is active. `process.poll()` returns `None`.  |
| `complete` | Subprocess exited with code 0. Results are available.        |
| `failed`   | Subprocess exited with non-zero code. stderr captured.       |

State transitions are determined by polling the subprocess. There are no intermediate states (such as "queued" or "cancelling") in this initial design.

### Scan Registry

The scan registry is a Python dictionary mapping scan IDs to scan records:

```python
scans: dict[str, ScanRecord] = {}
```

Each `ScanRecord` contains:

| Field          | Type                    | Description                                    |
|----------------|-------------------------|------------------------------------------------|
| `process`      | `subprocess.Popen`      | Handle to the CWAC subprocess                  |
| `config_path`  | `str`                   | Path to the generated config file              |
| `base_urls_dir`| `str`                   | Path to the generated base URLs directory      |
| `results_dir`  | `str`                   | Path where CWAC will write results             |
| `status`       | `str`                   | Current state: `running`, `complete`, `failed` |
| `start_time`   | `datetime`              | When the scan was initiated                    |
| `end_time`     | `datetime` or `None`    | When the scan completed (or failed)            |
| `audit_name`   | `str`                   | Human-readable name for this scan              |
| `stdout`       | `str`                   | Captured stdout from the subprocess            |
| `stderr`       | `str`                   | Captured stderr from the subprocess            |

Scan IDs are generated using UUID4 to ensure uniqueness without coordination.

### Interaction Pattern

A typical Claude Code workflow proceeds as follows:

1. **User:** "Scan example.com for accessibility issues"
2. **Claude Code** calls `cwac_scan(urls=["https://example.com"])`
3. **MCP server** generates config, launches subprocess, returns `{scan_id: "abc-123", status: "started"}`
4. **Claude Code** tells the user the scan has started
5. **Claude Code** periodically calls `cwac_scan_status(scan_id="abc-123")`
6. **MCP server** polls the subprocess, returns `{status: "running", elapsed_time: "45s"}`
7. Eventually the scan completes: `{status: "complete", elapsed_time: "2m 15s"}`
8. **Claude Code** calls `cwac_get_summary(scan_id="abc-123")` and `cwac_get_results(scan_id="abc-123")`
9. **Claude Code** presents the findings to the user

This pattern keeps each tool call short (sub-second for status checks) while supporting arbitrarily long scan durations.

## Alternatives Considered

### Alternative 1: Synchronous blocking scans

The simplest approach would be to have `cwac_scan` block until the scan completes and return all results directly:

```python
# Blocking approach (rejected)
def cwac_scan(urls):
    process = subprocess.run(["python", "cwac.py", config], cwd=CWAC_DIR)
    return read_results(results_dir)
```

**Why it was rejected:**

- Tool calls would block for minutes or hours. The user gets no feedback during this time.
- Claude Code cannot do anything else while waiting. The entire session is frozen.
- If the connection drops during a long scan, the results are lost even though the scan may have completed.
- There is no way to cancel a long-running scan.
- Multiple scan requests would serialize, making it impossible to run concurrent scans.

### Alternative 2: External job queue (Celery, Redis Queue)

Using a production job queue system would provide persistent state, automatic retries, and distributed execution:

**Why it was rejected:**

- Massive overengineering for a local development tool. Installing and configuring Redis, Celery, and a result backend adds significant infrastructure complexity.
- The MCP server runs on a developer's machine, not in a production cluster. The reliability guarantees of a job queue are not needed.
- Adds multiple new dependencies and potential failure points.
- The in-memory approach is sufficient for the expected use case (a single developer running occasional scans).

### Alternative 3: File-based state persistence

Storing scan state in files (JSON or SQLite) rather than in-memory would survive server restarts:

**Why it was rejected for now:**

- Adds file I/O overhead for every status check.
- Introduces potential file locking issues with concurrent access.
- The subprocess handle (`Popen` object) cannot be serialized; process monitoring would need to be rebuilt on restart.
- For the initial version, in-memory state is simpler and sufficient. Persistence can be added later if needed (see Future Considerations).

## Consequences

### Positive

- **Responsive interactions.** Every tool call returns quickly, keeping the conversational flow smooth.
- **Concurrent scans.** Multiple scans can run simultaneously, each tracked independently in the registry.
- **Progress visibility.** The user can check scan progress at any time without interrupting the scan.
- **Simple implementation.** An in-memory dictionary is the simplest possible state store, with no external dependencies.
- **Natural workflow.** The initiate/monitor/retrieve pattern matches how a human would interact with a long-running audit tool.

### Negative

- **State loss on restart.** If the MCP server crashes or is restarted, all scan tracking information is lost. Running subprocesses become orphaned (though their results will still be written to disk).
- **No scan cancellation.** The current design does not include a cancel/abort mechanism. This could be added as a future enhancement by calling `process.kill()`.
- **Resource contention.** Concurrent scans all use CWAC's shared directories (`./results/`). CWAC itself may not be designed for concurrent execution, and simultaneous scans could conflict if they produce results with overlapping names.
- **No automatic retry.** Failed scans are marked as failed but not retried. The user must manually initiate a new scan.
- **Memory growth.** Completed scan records remain in memory indefinitely. For long-running server sessions with many scans, this could become significant (though each record is small).

## Future Considerations

- **Scan cancellation tool:** Add a `cwac_cancel_scan` tool that calls `process.terminate()` or `process.kill()`.
- **State persistence:** If restart resilience becomes important, scan records could be serialized to a JSON file. The subprocess handle would need to be replaced with PID-based process tracking.
- **Orphan detection:** On server startup, scan the `./results/` directory for completed scans that are not in the registry and make them available through `cwac_list_scans`.
- **Resource limits:** Add a maximum concurrent scan count to prevent resource exhaustion.

## Dependencies

| Relationship  | Target   | Description                                            |
|---------------|----------|--------------------------------------------------------|
| DEPENDS_ON    | ADR-001  | Scan lifecycle is part of the MCP integration approach |
| DEPENDS_ON    | ADR-002  | Subprocess model defines how scans are executed        |

## Referenced Specification

| Spec ID    | Title                 | Version |
|------------|-----------------------|---------|
| SPEC-003-A | Scan Registry Design  | A       |

## Status History

| Date       | Status   | Changed By    | Notes                     |
|------------|----------|---------------|---------------------------|
| 2026-02-24 | Accepted | Chris Barlow  | Initial decision recorded |

## Governance

This ADR was authored following the WH(Y) decision format from [cgbarlow/adr](https://github.com/cgbarlow/adr). Changes to this decision require a new ADR that supersedes this one.
