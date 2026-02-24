# ADR-004: Plugin Architecture

| Field    | Value                                        |
|----------|----------------------------------------------|
| **ID**   | ADR-004                                      |
| **Status** | Accepted                                   |
| **Date** | 2026-02-24                                   |
| **Author** | Chris Barlow                               |

## WH(Y) Decision Statement

**In the context of** packaging di-test as a distributable Claude Code plugin so that other developers can install and use its accessibility scanning capabilities,

**facing** the need to choose a distribution model, plugin structure, and skill surface that balances simplicity with discoverability,

**we decided for** a same-repo marketplace model where `marketplace.json` lives in the di-test repository itself, plugin source is `"."`, the plugin manifest lives at `.claude-plugin/plugin.json`, and seven skills are exposed as slash commands (`/di-test:scan`, `/di-test:scan-status`, `/di-test:results`, `/di-test:summary`, `/di-test:report`, `/di-test:list-scans`, `/di-test:visual-scan`),

**and neglected** npm package distribution, a separate plugin repository, and a monorepo workspace layout,

**to achieve** zero-friction installation from a single repository, a clear mapping between skills and existing MCP tools, and a self-contained plugin that requires no external registry,

**accepting that** consumers must clone or reference the repository directly, and that future growth may eventually warrant a dedicated registry or package distribution.

## Context

The di-test platform currently provides accessibility scanning capabilities through two mechanisms: a CWAC MCP server (ADR-001) that exposes six tools for automated WCAG compliance scanning, and a Playwright MCP integration for visual pattern detection. These tools are available only when a developer manually configures their `.mcp.json` and has the correct dependencies installed.

Claude Code's plugin system provides a structured way to package tools, skills, hooks, and MCP server configurations into a single installable unit. Converting di-test into a plugin would allow any Claude Code user to install the accessibility scanning capabilities with a single command, without needing to understand the underlying MCP server configuration or dependency chain.

The core question is: **what distribution and packaging model should the di-test plugin use?**

## Decision

We will package di-test as a Claude Code plugin named `di-test` with the following structure:

### Plugin Manifest

The plugin manifest lives at `.claude-plugin/plugin.json` in the repository root. It declares the plugin's metadata, skills, hooks, MCP server configuration, and dependencies.

### Skills

Seven skills are exposed, each corresponding to an MCP tool or Playwright-based workflow:

| Skill              | Slash Command              | Underlying MCP Tool / Workflow         |
|--------------------|----------------------------|----------------------------------------|
| `scan`             | `/di-test:scan`            | `cwac_scan`                            |
| `scan-status`      | `/di-test:scan-status`     | `cwac_scan_status`                     |
| `results`          | `/di-test:results`         | `cwac_get_results`                     |
| `summary`          | `/di-test:summary`         | `cwac_get_summary`                     |
| `report`           | `/di-test:report`          | `cwac_generate_report`                 |
| `list-scans`       | `/di-test:list-scans`      | `cwac_list_scans`                      |
| `visual-scan`      | `/di-test:visual-scan`     | Playwright MCP browser tools           |

Each skill is defined in a `SKILL.md` file under `.claude-plugin/skills/{skill-name}/SKILL.md`.

### Marketplace Configuration

A `marketplace.json` file in the repository root registers the plugin for discovery. Because the plugin source code and the marketplace listing coexist in the same repository, the `source` field is `"."`, meaning the plugin is installed directly from the repository root.

### SessionStart Hook

A `SessionStart` hook runs during plugin initialisation to ensure all dependencies are installed. This hook:

1. Checks for Python dependencies required by the CWAC MCP server.
2. Verifies that CWAC is available at the expected path.
3. Installs npm dependencies if `package.json` exists.
4. Reports any missing dependencies to the user.

### MCP Server Registration

The plugin manifest declares the `cwac-mcp-server` as an MCP server dependency. When the plugin is installed, Claude Code automatically configures the MCP server in the user's environment, eliminating the need for manual `.mcp.json` edits.

## Rationale

### Why same-repo marketplace over alternatives

**Alternative 1: npm package distribution**

Publishing di-test as an npm package to the npm registry was considered. This would allow installation via `npm install -g di-test` or a Claude Code plugin install command:

- Requires maintaining a separate build and publish pipeline for the npm registry.
- The CWAC MCP server is Python-based; packaging Python dependencies inside an npm package creates a hybrid dependency problem that npm is not designed to solve.
- Versioning would need to be coordinated between the npm package, the Python MCP server, and CWAC itself.
- Users would need both npm and Python environments correctly configured, but the npm install process provides no mechanism to verify or set up the Python side.
- Adds a hard dependency on the npm registry being available, which is unnecessary for a tool that is currently used by a small, known user base.

**Alternative 2: Separate plugin repository**

Maintaining a dedicated repository (e.g., `cgbarlow/di-test-plugin`) that contains only the plugin manifest, skill definitions, and marketplace configuration, with the actual tool code remaining in the di-test repository, was considered:

- Splits the codebase across two repositories, requiring coordinated changes when skills or tools are modified.
- The plugin manifest references MCP server paths that are relative to the di-test repository, creating fragile cross-repository path dependencies.
- Doubles the maintenance burden for issues, pull requests, and releases.
- Provides no meaningful benefit in separation of concerns, since the skills are tightly coupled to the MCP tools they invoke.

**Alternative 3: Monorepo workspace layout**

Structuring di-test as a monorepo with separate workspaces for the MCP server, plugin, and scanner was considered:

- Adds significant tooling overhead (workspace configuration, cross-workspace dependency management, hoisted vs. isolated dependencies).
- The project is not large enough to benefit from monorepo patterns; the additional structure would slow down development rather than improve it.
- Monorepo tooling (Lerna, Turborepo, npm workspaces) is designed for JavaScript/TypeScript projects and does not naturally accommodate the Python CWAC MCP server.

**Why same-repo wins:**

The same-repo model is the simplest approach that satisfies all requirements:

1. **Single source of truth.** The plugin manifest, skill definitions, MCP server code, and marketplace configuration all live in one repository. A change to a tool is immediately reflected in the corresponding skill without cross-repository synchronisation.

2. **Zero build step.** The plugin is installed directly from the repository. There is no compilation, transpilation, or packaging step. The source code is the distributable.

3. **Python-friendly.** The model makes no assumptions about the language ecosystem. The `SessionStart` hook can install Python dependencies just as easily as npm dependencies.

4. **Low barrier to contribution.** A contributor clones one repository and has everything needed to develop, test, and modify the plugin.

5. **Future-proof.** If the project grows to the point where a dedicated registry or npm distribution is warranted, the same-repo model can be migrated to a more sophisticated distribution model without redesigning the plugin's internal structure.

## Consequences

### Positive

- Any Claude Code user can install the di-test plugin from a single repository reference.
- Skills provide a conversational interface to accessibility scanning, with tab-completion and discoverability via `/di-test:`.
- The `SessionStart` hook ensures dependencies are installed before any skill is invoked, reducing "it doesn't work" issues.
- MCP server configuration is bundled with the plugin, eliminating manual `.mcp.json` editing.
- The marketplace.json enables future plugin discovery mechanisms without requiring changes to the plugin itself.

### Negative

- Users must have access to the repository (public or authorised) to install the plugin.
- The same-repo model does not support independent versioning of the plugin manifest versus the tool code; they are always in lockstep.
- The `SessionStart` hook adds latency to session startup while dependency checks run.
- There is no centralised plugin registry; discovery depends on knowing the repository URL.

## Dependencies

| Relationship  | Target   | Description                                                |
|---------------|----------|------------------------------------------------------------|
| EXTENDS       | ADR-001  | Wraps CWAC MCP tools as plugin skills                      |
| RELATES_TO    | ADR-000  | Visual scan skill uses Playwright-based pattern detection   |
| RELATES_TO    | ADR-003  | Scan lifecycle tools exposed as plugin skills               |

## Referenced Specification

| Spec ID    | Title                            | Version |
|------------|----------------------------------|---------|
| SPEC-004-A | Plugin Manifest and Skill Definitions | A  |

## Status History

| Date       | Status   | Changed By    | Notes                     |
|------------|----------|---------------|---------------------------|
| 2026-02-24 | Accepted | Chris Barlow  | Initial decision recorded |

## Governance

This ADR was authored following the WH(Y) decision format from [cgbarlow/adr](https://github.com/cgbarlow/adr). Changes to this decision require a new ADR that supersedes this one.
