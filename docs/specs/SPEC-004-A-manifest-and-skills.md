# SPEC-004-A: Plugin Manifest and Skill Definitions

| Field           | Value                                        |
|-----------------|----------------------------------------------|
| **Parent ADR**  | ADR-004 (Plugin Architecture)                |
| **Version**     | A (initial)                                  |
| **Status**      | Accepted                                     |
| **Date**        | 2026-02-24                                   |

## Overview

This specification defines the plugin manifest schema (`plugin.json`), the skill definition format (`SKILL.md`), the marketplace configuration (`marketplace.json`), and the MCP server registration for the di-test Claude Code plugin. Together these components allow Claude Code to discover, install, and invoke the di-test accessibility scanning capabilities through a structured plugin interface.

The plugin exposes seven skills that map to the underlying CWAC MCP tools and Playwright-based visual scanning workflows. Each skill is invokable as a slash command (e.g., `/di-test:scan`) and is defined in a dedicated `SKILL.md` file that provides Claude Code with the context needed to execute the skill correctly.

---

## 1. Plugin Manifest (`plugin.json`)

### 1.1 File Location

The plugin manifest is located at `.claude-plugin/plugin.json` relative to the repository root.

### 1.2 Schema

```json
{
  "name": "di-test",
  "version": "1.0.0",
  "description": "Accessibility testing plugin for Claude Code. Runs WCAG compliance scans using CWAC and visual pattern detection using Playwright.",
  "author": "Chris Barlow",
  "skills": [
    {
      "name": "scan",
      "path": "skills/scan/SKILL.md"
    },
    {
      "name": "scan-status",
      "path": "skills/scan-status/SKILL.md"
    },
    {
      "name": "results",
      "path": "skills/results/SKILL.md"
    },
    {
      "name": "summary",
      "path": "skills/summary/SKILL.md"
    },
    {
      "name": "report",
      "path": "skills/report/SKILL.md"
    },
    {
      "name": "list-scans",
      "path": "skills/list-scans/SKILL.md"
    },
    {
      "name": "visual-scan",
      "path": "skills/visual-scan/SKILL.md"
    }
  ],
  "hooks": {
    "SessionStart": {
      "command": "bash .claude-plugin/hooks/session-start.sh",
      "description": "Verify and install dependencies for the CWAC MCP server and Playwright."
    }
  },
  "mcpServers": {
    "cwac-mcp-server": {
      "command": "node",
      "args": ["cwac-mcp-server/build/index.js"],
      "env": {
        "CWAC_PATH": "/workspaces/cwac"
      }
    }
  },
  "dependencies": {
    "runtime": {
      "node": ">=18.0.0",
      "python": ">=3.10"
    },
    "python": [
      "cwac"
    ],
    "system": [
      "chromium"
    ]
  }
}
```

### 1.3 Field Definitions

| Field          | Type     | Required | Description                                                                                          |
|----------------|----------|----------|------------------------------------------------------------------------------------------------------|
| `name`         | `string` | Yes      | The plugin identifier. Used as the namespace prefix for skill invocation (e.g., `/di-test:scan`).    |
| `version`      | `string` | Yes      | Semantic version of the plugin. Follows semver (`MAJOR.MINOR.PATCH`).                                |
| `description`  | `string` | Yes      | Human-readable description displayed during plugin discovery and installation.                        |
| `author`       | `string` | Yes      | The plugin author's name.                                                                            |
| `skills`       | `array`  | Yes      | Array of skill registration objects. Each object contains `name` (string) and `path` (string) fields. The `path` is relative to `.claude-plugin/`. |
| `hooks`        | `object` | No       | Lifecycle hooks. Keys are hook names (e.g., `SessionStart`). Values are objects with `command` (string) and optional `description` (string). |
| `mcpServers`   | `object` | No       | MCP server definitions to register when the plugin is installed. Follows the same schema as `.mcp.json` server entries. |
| `dependencies` | `object` | No       | Dependency declarations used by the `SessionStart` hook and plugin installer to verify the environment. |

### 1.4 Skills Array

Each entry in the `skills` array registers a skill with Claude Code:

| Field  | Type     | Required | Description                                                                                  |
|--------|----------|----------|----------------------------------------------------------------------------------------------|
| `name` | `string` | Yes      | The skill name. Combined with the plugin name to form the slash command: `/di-test:{name}`.  |
| `path` | `string` | Yes      | Relative path from `.claude-plugin/` to the skill's `SKILL.md` file.                        |

### 1.5 Hooks Object

The `hooks` object supports the following lifecycle events:

| Hook Name      | Trigger                                | Description                                        |
|----------------|----------------------------------------|----------------------------------------------------|
| `SessionStart` | When a Claude Code session begins      | Runs dependency checks and installation routines.  |

Each hook value is an object:

| Field         | Type     | Required | Description                                                        |
|---------------|----------|----------|--------------------------------------------------------------------|
| `command`     | `string` | Yes      | Shell command to execute. Runs from the plugin's root directory.   |
| `description` | `string` | No       | Human-readable description of what the hook does.                  |

### 1.6 MCP Servers Object

The `mcpServers` object declares MCP servers that should be registered in the user's environment when the plugin is installed. Each key is a server name and each value follows the standard MCP server configuration schema:

| Field     | Type              | Required | Description                                                   |
|-----------|-------------------|----------|---------------------------------------------------------------|
| `command` | `string`          | Yes      | The executable to run (e.g., `node`, `python`).               |
| `args`    | `array` of `string` | Yes    | Arguments passed to the command.                              |
| `env`     | `object`          | No       | Environment variables set for the server process.             |

### 1.7 Dependencies Object

The `dependencies` object provides structured declarations for the plugin's external requirements:

| Field     | Type     | Description                                                                          |
|-----------|----------|--------------------------------------------------------------------------------------|
| `runtime` | `object` | Minimum runtime versions. Keys are runtime names (e.g., `node`, `python`); values are semver range strings. |
| `python`  | `array`  | Python package names required by the plugin.                                         |
| `system`  | `array`  | System-level dependencies that must be available on the host (e.g., `chromium`).     |

---

## 2. Skill Definitions (SKILL.md Format)

### 2.1 File Location

Each skill is defined in a `SKILL.md` file at `.claude-plugin/skills/{skill-name}/SKILL.md`. The directory name matches the skill name declared in `plugin.json`.

### 2.2 SKILL.md Format

Every `SKILL.md` follows a consistent structure that provides Claude Code with enough context to understand when and how to invoke the skill. The format is:

```markdown
---
description: Short, one-line description of what the skill does.
---

# {Skill Name}

## Description

A paragraph describing the skill's purpose, when to use it, and what it produces.

## Usage

Invocation examples showing how a user triggers the skill.

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| ...       | ...  | ...      | ...     | ...         |

## Examples

Concrete examples of skill invocations with expected behaviour.

## Related MCP Tools

| Tool Name | Relationship | Description |
|-----------|-------------|-------------|
| ...       | ...         | ...         |
```

### 2.3 Skill: `scan`

**File:** `.claude-plugin/skills/scan/SKILL.md`

| Field            | Value                                                                 |
|------------------|-----------------------------------------------------------------------|
| **Description**  | Start a CWAC accessibility scan against one or more URLs.             |
| **Slash Command**| `/di-test:scan`                                                       |

**Parameters:**

| Parameter              | Type                        | Required | Default             | Description                                              |
|------------------------|-----------------------------|----------|---------------------|----------------------------------------------------------|
| `urls`                 | space-separated URL list    | Yes      | --                  | One or more URLs to scan.                                |
| `--name`               | `string`                    | No       | Auto-generated      | Human-readable audit name.                               |
| `--plugins`            | comma-separated list        | No       | All enabled         | CWAC plugins to enable (e.g., `axe_core_audit,html_validation`). |
| `--max-links`          | `integer`                   | No       | `50`                | Maximum links to follow per domain.                      |

**Usage Examples:**

```
/di-test:scan https://example.com
/di-test:scan https://example.com https://example.com/about --name "Example Audit"
/di-test:scan https://example.com --plugins axe_core_audit --max-links 20
```

**Related MCP Tools:**

| Tool Name    | Relationship | Description                          |
|--------------|-------------|--------------------------------------|
| `cwac_scan`  | Invokes     | Starts the CWAC scan subprocess.     |

### 2.4 Skill: `scan-status`

**File:** `.claude-plugin/skills/scan-status/SKILL.md`

| Field            | Value                                                       |
|------------------|-------------------------------------------------------------|
| **Description**  | Check the status of a running or completed CWAC scan.       |
| **Slash Command**| `/di-test:scan-status`                                      |

**Parameters:**

| Parameter  | Type     | Required | Default        | Description                             |
|------------|----------|----------|----------------|-----------------------------------------|
| `scan_id`  | `string` | No       | Most recent    | The scan ID to check. Defaults to the most recently started scan. |

**Usage Examples:**

```
/di-test:scan-status
/di-test:scan-status a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

**Related MCP Tools:**

| Tool Name           | Relationship | Description                              |
|---------------------|-------------|------------------------------------------|
| `cwac_scan_status`  | Invokes     | Polls the scan subprocess for status.    |

### 2.5 Skill: `results`

**File:** `.claude-plugin/skills/results/SKILL.md`

| Field            | Value                                                              |
|------------------|--------------------------------------------------------------------|
| **Description**  | Retrieve detailed results from a completed CWAC scan.              |
| **Slash Command**| `/di-test:results`                                                 |

**Parameters:**

| Parameter      | Type     | Required | Default     | Description                                                        |
|----------------|----------|----------|-------------|--------------------------------------------------------------------|
| `scan_id`      | `string` | No       | Most recent | The scan ID to retrieve results for.                               |
| `--audit-type` | `string` | No       | All types   | Filter by audit type (e.g., `axe_core_audit`, `html_validation`). |
| `--impact`     | `string` | No       | All impacts | Filter by impact level: `critical`, `serious`, `moderate`, `minor`.|
| `--limit`      | `integer`| No       | `100`       | Maximum number of results to return.                               |

**Usage Examples:**

```
/di-test:results
/di-test:results a1b2c3d4 --audit-type axe_core_audit --impact critical
/di-test:results --limit 50
```

**Related MCP Tools:**

| Tool Name          | Relationship | Description                                  |
|--------------------|-------------|----------------------------------------------|
| `cwac_get_results` | Invokes     | Reads and filters CSV result files to JSON.  |

### 2.6 Skill: `summary`

**File:** `.claude-plugin/skills/summary/SKILL.md`

| Field            | Value                                                              |
|------------------|--------------------------------------------------------------------|
| **Description**  | Get an aggregated summary of findings from a completed scan.       |
| **Slash Command**| `/di-test:summary`                                                 |

**Parameters:**

| Parameter  | Type     | Required | Default        | Description                             |
|------------|----------|----------|----------------|-----------------------------------------|
| `scan_id`  | `string` | No       | Most recent    | The scan ID to summarise.               |

**Usage Examples:**

```
/di-test:summary
/di-test:summary a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

**Related MCP Tools:**

| Tool Name          | Relationship | Description                                       |
|--------------------|-------------|---------------------------------------------------|
| `cwac_get_summary` | Invokes     | Aggregates scan results into counts and rankings. |

### 2.7 Skill: `report`

**File:** `.claude-plugin/skills/report/SKILL.md`

| Field            | Value                                                              |
|------------------|--------------------------------------------------------------------|
| **Description**  | Generate a leaderboard report from completed scan data.            |
| **Slash Command**| `/di-test:report`                                                  |

**Parameters:**

| Parameter  | Type     | Required | Default        | Description                             |
|------------|----------|----------|----------------|-----------------------------------------|
| `scan_id`  | `string` | No       | Most recent    | The scan ID to generate a report for.   |

**Usage Examples:**

```
/di-test:report
/di-test:report a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

**Related MCP Tools:**

| Tool Name              | Relationship | Description                                         |
|------------------------|-------------|-----------------------------------------------------|
| `cwac_generate_report` | Invokes     | Runs CWAC's report generation script.               |

### 2.8 Skill: `list-scans`

**File:** `.claude-plugin/skills/list-scans/SKILL.md`

| Field            | Value                                                              |
|------------------|--------------------------------------------------------------------|
| **Description**  | List all available scan results, including scans from previous sessions. |
| **Slash Command**| `/di-test:list-scans`                                              |

**Parameters:**

This skill takes no parameters.

**Usage Examples:**

```
/di-test:list-scans
```

**Related MCP Tools:**

| Tool Name          | Relationship | Description                                      |
|--------------------|-------------|--------------------------------------------------|
| `cwac_list_scans`  | Invokes     | Enumerates the CWAC results directory.           |

### 2.9 Skill: `visual-scan`

**File:** `.claude-plugin/skills/visual-scan/SKILL.md`

| Field            | Value                                                                     |
|------------------|---------------------------------------------------------------------------|
| **Description**  | Perform a visual accessibility scan using Playwright browser automation.  |
| **Slash Command**| `/di-test:visual-scan`                                                    |

**Parameters:**

| Parameter     | Type     | Required | Default              | Description                                                  |
|---------------|----------|----------|----------------------|--------------------------------------------------------------|
| `url`         | `string` | Yes      | --                   | The URL to visually scan.                                    |
| `--checks`    | comma-separated list | No | All checks     | Specific visual checks to run (e.g., `headings,cards,forms`).|
| `--viewport`  | `string` | No       | `1280x720`           | Viewport size in `WIDTHxHEIGHT` format.                     |

**Usage Examples:**

```
/di-test:visual-scan https://example.com
/di-test:visual-scan https://example.com --checks headings,cards
/di-test:visual-scan https://example.com --viewport 375x812
```

**Related MCP Tools:**

| Tool Name                          | Relationship | Description                                            |
|------------------------------------|-------------|--------------------------------------------------------|
| `mcp__playwright__browser_navigate`| Uses        | Navigates Playwright browser to the target URL.        |
| `mcp__playwright__browser_snapshot`| Uses        | Captures accessibility snapshot for analysis.          |
| `mcp__playwright__browser_take_screenshot` | Uses | Takes visual screenshot for pattern detection.  |

---

## 3. Marketplace Configuration

### 3.1 File Location

The marketplace configuration is located at `marketplace.json` in the repository root.

### 3.2 Schema

```json
{
  "plugins": [
    {
      "name": "di-test",
      "version": "1.0.0",
      "description": "Accessibility testing plugin for Claude Code. Runs WCAG compliance scans using CWAC and visual pattern detection using Playwright.",
      "author": "Chris Barlow",
      "source": ".",
      "tags": ["accessibility", "wcag", "testing", "a11y", "cwac"],
      "license": "MIT"
    }
  ]
}
```

### 3.3 Field Definitions

| Field         | Type              | Required | Description                                                                  |
|---------------|-------------------|----------|------------------------------------------------------------------------------|
| `plugins`     | `array`           | Yes      | Array of plugin entries in this marketplace.                                 |
| `name`        | `string`          | Yes      | Must match the `name` field in `plugin.json`.                                |
| `version`     | `string`          | Yes      | Must match the `version` field in `plugin.json`.                             |
| `description` | `string`          | Yes      | Short description for marketplace listing.                                   |
| `author`      | `string`          | Yes      | Plugin author name.                                                          |
| `source`      | `string`          | Yes      | Path to the plugin root relative to the marketplace file. `"."` means the plugin is in the same repository as the marketplace. |
| `tags`        | `array` of `string` | No     | Searchable tags for plugin discovery.                                        |
| `license`     | `string`          | No       | SPDX license identifier.                                                     |

### 3.4 Same-Repo Model

In the same-repo marketplace model, the `source` field is `"."` because the plugin manifest (`.claude-plugin/plugin.json`) is located in the same repository as the `marketplace.json` file. This eliminates the need for external URLs or package registry references. When a user installs from this marketplace, the plugin installer resolves `"."` to the repository root and locates `.claude-plugin/plugin.json` from there.

---

## 4. MCP Server Registration

### 4.1 Automatic Registration

When the di-test plugin is installed, the `mcpServers` section of `plugin.json` is merged into the user's MCP configuration. This means the user does not need to manually edit `.mcp.json` to register the CWAC MCP server.

### 4.2 Server Configuration

The plugin registers one MCP server:

| Server Name        | Command | Args                              | Environment                          |
|--------------------|---------|-----------------------------------|--------------------------------------|
| `cwac-mcp-server`  | `node`  | `["cwac-mcp-server/build/index.js"]` | `CWAC_PATH=/workspaces/cwac`      |

### 4.3 Existing Playwright MCP Server

The Playwright MCP server is not registered by the plugin because it is expected to be installed independently as a general-purpose browser automation tool. The `visual-scan` skill assumes the Playwright MCP server is already available. If it is not present, the skill will report an error indicating that Playwright MCP must be installed separately.

### 4.4 Server Lifecycle

The MCP server process is managed by Claude Code's MCP runtime:

1. **Startup.** The server is started automatically when Claude Code initialises and detects the plugin's MCP server declaration.
2. **Communication.** The server uses stdio transport. Claude Code communicates with it via stdin/stdout using the MCP protocol.
3. **Shutdown.** The server process is terminated when the Claude Code session ends.
4. **Restart.** If the server process crashes, Claude Code may restart it automatically depending on its MCP server management policy.

### 4.5 SessionStart Hook Detail

The `SessionStart` hook defined in `plugin.json` executes `.claude-plugin/hooks/session-start.sh` at the beginning of each Claude Code session. The hook performs the following checks:

1. **Node.js version check.** Verifies `node --version` meets the `>=18.0.0` requirement.
2. **Python version check.** Verifies `python3 --version` meets the `>=3.10` requirement.
3. **CWAC availability.** Checks that the CWAC installation exists at the path specified by `CWAC_PATH`.
4. **npm dependencies.** Runs `npm install` in the plugin root if `node_modules` is missing or stale.
5. **Python dependencies.** Verifies that required Python packages are importable.
6. **Chromium availability.** Checks that a Chromium binary is available for Playwright.

If any check fails, the hook outputs a diagnostic message indicating what is missing and how to resolve it. The hook exits with code 0 even on soft failures (missing optional dependencies) but exits with a non-zero code if critical dependencies (Node.js, Python, CWAC) are missing.

---

## Related Specifications

| Spec ID    | Relationship | Title                      |
|------------|-------------|----------------------------|
| SPEC-001-A | Extends     | MCP Tool Definitions       |
| SPEC-000-A | Extends     | Visual Pattern Scanner     |
| SPEC-002-A | References  | Subprocess Execution Model |
| SPEC-003-A | References  | Scan Registry Design       |

## Changelog

| Version | Date       | Author        | Changes                          |
|---------|------------|---------------|----------------------------------|
| A       | 2026-02-24 | Chris Barlow  | Initial specification            |
