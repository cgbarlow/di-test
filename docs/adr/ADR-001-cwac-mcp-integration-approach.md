# ADR-001: CWAC MCP Integration Approach

| Field    | Value                                        |
|----------|----------------------------------------------|
| **ID**   | ADR-001                                      |
| **Status** | Accepted                                   |
| **Date** | 2026-02-24                                   |
| **Author** | Chris Barlow                               |

## WH(Y) Decision Statement

**In the context of** the di-test accessibility testing platform needing automated CWAC scan capabilities,

**facing** the need to invoke CWAC audits programmatically from Claude Code without manual CLI intervention,

**we decided for** an MCP server wrapper that exposes CWAC functionality as MCP tools,

**and neglected** direct REST API wrapper, shell script integration, and manual CLI invocation,

**to achieve** seamless Claude Code integration, structured tool parameters, and real-time scan management,

**accepting that** an additional server process is required and CWAC must be installed alongside.

## Context

The [GOVTNZ/cwac](https://github.com/GOVTNZ/cwac) (Check Website Accessibility Compliance) tool is a Python-based accessibility scanner used by New Zealand government agencies to audit websites against WCAG criteria. It runs axe-core audits, HTML validation, and other checks across multiple pages, producing CSV result files.

The di-test platform already uses Playwright MCP for browser-based visual pattern detection. Adding CWAC capabilities would give Claude Code the ability to run comprehensive WCAG compliance scans alongside the existing heading and card detection features, providing a complete accessibility audit workflow within a single conversational interface.

The core question is: **how should CWAC be made available to Claude Code?**

## Decision

We will build a dedicated MCP server (`cwac-mcp-server`) that wraps CWAC's functionality and exposes it through six MCP tools:

| Tool                    | Purpose                                      |
|-------------------------|----------------------------------------------|
| `cwac_scan`             | Start a new CWAC accessibility scan          |
| `cwac_scan_status`      | Check the status of a running scan           |
| `cwac_get_results`      | Retrieve scan results with filtering         |
| `cwac_get_summary`      | Get an aggregated summary of scan findings   |
| `cwac_list_scans`       | List all available scan results              |
| `cwac_generate_report`  | Generate leaderboard reports from scan data  |

The server runs as a standard MCP stdio server, configured in `.mcp.json` alongside the existing Playwright MCP server.

## Rationale

### Why MCP over alternatives

**Alternative 1: Direct REST API wrapper**

Wrapping CWAC in a Flask or FastAPI REST server was considered. While this would make CWAC accessible over HTTP, it introduces unnecessary infrastructure for a local development tool:

- Requires managing a separate HTTP server process, port allocation, and health checks.
- Claude Code has no native HTTP client tool; invoking REST endpoints would require shell commands (`curl`) or custom tool definitions.
- Request/response schemas would need to be documented separately from tool definitions.
- No built-in mechanism for Claude Code to discover available endpoints or parameter types.

**Alternative 2: Shell script integration**

Wrapping CWAC invocations in bash scripts that Claude Code calls via its shell tool was considered:

- Shell scripts provide no structured parameter validation; all arguments are strings.
- Error handling is primitive (exit codes only, no structured error responses).
- Output parsing falls entirely on the LLM, increasing token usage and error rates.
- No discoverability; Claude Code cannot inspect what scripts are available or what parameters they accept.

**Alternative 3: Manual CLI invocation**

Having the user (or Claude Code via shell) run `python cwac.py` directly:

- Requires knowledge of CWAC's config file format, directory structure, and invocation patterns.
- No way to track scan progress or manage multiple concurrent scans.
- Results must be manually located and parsed from CSV files.
- Completely breaks the conversational workflow.

**Why MCP wins:**

MCP (Model Context Protocol) was designed specifically for this use case: giving LLM agents structured access to external tools. The advantages are:

1. **Structured tool definitions.** Each tool has a JSON schema defining its parameters with types, descriptions, and validation rules. Claude Code can inspect these schemas to understand what parameters are available before invoking a tool.

2. **Type-safe parameters.** Parameters are typed (string, integer, boolean, object, array) rather than being flattened into command-line strings. This eliminates an entire class of invocation errors.

3. **Native Claude Code integration.** MCP servers are first-class citizens in Claude Code's architecture. They appear in the tool palette, are included in system prompts, and benefit from Claude's tool-use training.

4. **Structured responses.** Tool results are returned as structured JSON, not raw stdout. This means results can be parsed, filtered, and presented without brittle text extraction.

5. **Discoverability.** Claude Code automatically discovers available tools when the MCP server starts. There is no need for separate documentation or prompt engineering to teach the model what tools exist.

6. **Process lifecycle management.** The MCP server manages CWAC subprocess lifecycles, including scan initiation, progress monitoring, and cleanup. This complexity is encapsulated away from the conversational interface.

### Tool design rationale

The six tools follow a scan lifecycle pattern rather than mirroring CWAC's internal structure:

- **Initiate** (`cwac_scan`): Start a scan with high-level parameters (URLs, plugins, options). The tool handles config generation, directory setup, and subprocess launch internally.
- **Monitor** (`cwac_scan_status`): Poll scan progress. Returns elapsed time and recent stdout for user feedback.
- **Retrieve** (`cwac_get_results`, `cwac_get_summary`): Access results with filtering and aggregation. Converts CWAC's CSV output to structured JSON.
- **Browse** (`cwac_list_scans`): Discover existing scan results, including those from previous sessions or direct CLI runs.
- **Report** (`cwac_generate_report`): Generate formatted reports using CWAC's built-in reporting.

This separation allows Claude Code to start a scan, continue with other work, check back on progress, and then retrieve and analyse results -- mirroring the natural workflow of an accessibility auditor.

## Consequences

### Positive

- Claude Code can invoke CWAC scans conversationally without the user needing to know CWAC's CLI interface.
- Scan parameters are validated at the tool level before reaching CWAC.
- Results are returned as structured JSON, enabling Claude Code to analyse, summarise, and cross-reference findings.
- The MCP server can be reused by any MCP-compatible client, not just Claude Code.
- CWAC updates can be adopted without changing the MCP interface (as long as CLI and output formats remain stable).

### Negative

- An additional server process must be running alongside Claude Code.
- The MCP server must be maintained as CWAC evolves.
- There is a layer of indirection between the user and CWAC, which may complicate debugging.
- The server currently supports only stdio transport; network-based MCP transport would require additional work.

## Dependencies

| Relationship  | Target   | Description                                            |
|---------------|----------|--------------------------------------------------------|
| RELATES_TO    | ADR-002  | Subprocess execution model for running CWAC            |
| RELATES_TO    | ADR-003  | Scan lifecycle and registry design                     |

## Referenced Specification

| Spec ID    | Title                | Version |
|------------|----------------------|---------|
| SPEC-001-A | MCP Tool Definitions | A       |

## Status History

| Date       | Status   | Changed By    | Notes                     |
|------------|----------|---------------|---------------------------|
| 2026-02-24 | Accepted | Chris Barlow  | Initial decision recorded |

## Governance

This ADR was authored following the WH(Y) decision format from [cgbarlow/adr](https://github.com/cgbarlow/adr). Changes to this decision require a new ADR that supersedes this one.
