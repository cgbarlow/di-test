# ADR-006: Dependency Management

| Field    | Value                                        |
|----------|----------------------------------------------|
| **ID**   | ADR-006                                      |
| **Status** | Accepted                                   |
| **Date** | 2026-02-24                                   |
| **Author** | Chris Barlow                               |

## WH(Y) Decision Statement

**In the context of** a Claude Code plugin that depends on Python packages (`mcp[cli]`, `python-docx`, `jinja2`), Node.js packages (Playwright), and an external CWAC installation,

**facing** the need for zero-friction first-run setup where dependencies are installed automatically without manual intervention,

**we decided for** a SessionStart hook that runs `scripts/install-deps.sh` with a cascading CWAC_PATH discovery chain (environment variable, sibling directory, `/workspaces/cwac` fallback),

**and neglected** bundling CWAC into the plugin, Docker containerisation, publishing the plugin as a pip-installable package, and using conda environments,

**to achieve** automatic idempotent dependency installation, flexible CWAC location discovery, and a self-contained plugin that works across development environments,

**accepting that** CWAC must be installed separately, the SessionStart hook adds a few seconds to first launch, and the fallback chain assumes a specific workspace layout.

## Context

The di-test plugin comprises two distinct runtime environments:

1. **Python** -- the CWAC MCP server (`cwac_mcp/`) uses `mcp[cli]` for the MCP SDK, `python-docx` for Word document report generation, and `jinja2` for report templating. These are listed in `cwac_mcp/requirements.txt`.
2. **Node.js** -- Playwright is used by the visual pattern scanner and the Playwright MCP server. It is managed via `package.json` and requires browser binaries.

Additionally, the plugin depends on an external installation of [GOVTNZ/cwac](https://github.com/GOVTNZ/cwac), which is a standalone Python project with its own dependencies, configuration files, and data directories. CWAC is not published to PyPI and cannot be trivially bundled.

The core challenge is: **how do we ensure all dependencies are available when Claude Code starts a session, without requiring the user to run manual installation steps?**

Claude Code provides a `SessionStart` hook mechanism that executes a command automatically when a new session begins. This is the natural integration point for dependency bootstrapping.

## Decision

We will manage dependencies through the following architecture:

### 1. SessionStart Hook

The `.claude/settings.json` file configures a `SessionStart` hook that runs `scripts/install-deps.sh` at the start of every Claude Code session.

### 2. Python Dependencies via requirements.txt

All Python dependencies are declared in `cwac_mcp/requirements.txt`:

```
mcp[cli]
python-docx
jinja2
```

The install script runs `pip install -r cwac_mcp/requirements.txt` with a skip-if-installed check to avoid redundant work on subsequent sessions.

### 3. CWAC_PATH Discovery Chain

The plugin locates the external CWAC installation using a three-step fallback chain:

| Priority | Method                     | Path                                  |
|----------|----------------------------|---------------------------------------|
| 1        | `CWAC_PATH` environment variable | Value of `$CWAC_PATH`            |
| 2        | Sibling directory          | `../cwac` relative to the plugin root |
| 3        | Hardcoded fallback         | `/workspaces/cwac`                    |

The first path that exists and contains `cwac.py` is used. If none are valid, the server exits with a clear error message.

### 4. Node.js Dependencies

Playwright and its browser binaries are managed separately via npm. The `package.json` declares `@playwright/test` as a dependency. Browser installation is handled by `npx playwright install` within the install script.

### 5. Plugin Self-Containment

The plugin is self-contained in the `di-test` repository. All Python source code, MCP server definitions, configuration templates, and documentation live within the repository. The only external dependency is CWAC itself, which is discovered rather than bundled.

## Rationale

### Why SessionStart hook over manual setup

Manual setup instructions ("run `pip install -r requirements.txt` before starting") are fragile. Users forget, documentation goes stale, and new contributors hit cryptic import errors. The SessionStart hook makes installation automatic and invisible -- the plugin "just works" when Claude Code opens the project.

### Why a shell script over inline commands

The hook calls a dedicated `scripts/install-deps.sh` script rather than inline pip/npm commands because:

- The script can implement idempotency checks (skip if already installed).
- Error handling and logging are cleaner in a script than in a single-line hook.
- The script can be run manually for debugging (`bash scripts/install-deps.sh`).
- Future dependencies can be added without modifying the hook configuration.

### Why a CWAC_PATH discovery chain

CWAC is not a pip package and cannot be declared as a Python dependency. Different environments place CWAC in different locations:

- **GitHub Codespaces**: `/workspaces/cwac` (sibling to `/workspaces/di-test`).
- **Local development**: Wherever the developer cloned it, specified via `$CWAC_PATH`.
- **CI/CD**: Controlled via environment variables.

The three-step chain supports all these scenarios without requiring configuration.

### Alternatives rejected

**Alternative 1: Bundled CWAC**

Copying CWAC into the di-test repository (as a subtree or submodule) was considered:

- CWAC is a large, independently versioned project with its own dependencies. Bundling would create a maintenance burden to keep the copy in sync.
- CWAC's license and governance are separate from di-test. Copying the full codebase raises attribution and update concerns.
- CWAC requires its own data directories (`config/`, `base_urls/`, `results/`) with specific structures. These do not fit naturally inside the plugin tree.
- Git submodules add complexity to cloning and updating that conflicts with the zero-friction goal.

**Alternative 2: Docker containerisation**

Packaging the entire plugin (and CWAC) in a Docker container was considered:

- Docker adds significant complexity for what is fundamentally a development tool. Developers would need Docker installed, running, and configured.
- Claude Code's MCP server communication assumes local processes; running inside Docker requires network bridge configuration or volume mounts that complicate the setup.
- The Codespaces environment already provides a consistent base; Docker-in-Docker adds overhead without proportional benefit.
- Iterative development (editing code and restarting the server) is slower with container rebuilds.

**Alternative 3: pip install of plugin itself**

Publishing di-test as a pip package (with `setup.py` or `pyproject.toml`) and having users install it via `pip install di-test` was considered:

- The plugin is not a reusable library; it is a project-specific Claude Code configuration. Publishing to PyPI creates packaging overhead for a single-use tool.
- The Node.js dependencies (Playwright) cannot be expressed as pip dependencies, so a pip install would only partially solve the problem.
- The MCP server must be run from the project directory (to access `.mcp.json`, templates, and report assets). A pip-installed entry point would need to locate these files, adding complexity.

**Alternative 4: Conda environment**

Using conda (or mamba) to manage a complete environment with both Python and system dependencies was considered:

- Conda is not available by default in GitHub Codespaces, requiring additional setup.
- The environment file (`environment.yml`) cannot express the CWAC external dependency.
- Conda environments are heavier than pip for a project with only three Python dependencies.
- Claude Code has no native conda integration; the SessionStart hook would still be needed to activate the environment.

## Consequences

### Positive

- New contributors can start using the plugin immediately -- `claude` in the project directory is all that is needed.
- Dependencies are version-pinned in `requirements.txt`, ensuring reproducible environments.
- The CWAC_PATH discovery chain works across Codespaces, local development, and CI without configuration.
- The install script is idempotent; repeated runs are fast and safe.
- Python and Node.js dependency management are cleanly separated.

### Negative

- The SessionStart hook adds a few seconds to session startup (mitigated by skip-if-installed checks).
- CWAC must be installed separately; there is no single command that sets up everything.
- The fallback chain assumes Codespaces conventions (`/workspaces/`); non-standard layouts require setting `CWAC_PATH` explicitly.
- The install script must be maintained as dependencies change.
- pip installs into the system Python (or active virtualenv); there is no enforced isolation between the plugin's dependencies and other projects.

## Dependencies

| Relationship  | Target   | Description                                            |
|---------------|----------|--------------------------------------------------------|
| RELATES_TO    | ADR-001  | MCP server requires mcp[cli] dependency                |
| RELATES_TO    | ADR-002  | Subprocess execution depends on CWAC_PATH discovery    |

## Referenced Specification

| Spec ID    | Title                      | Version |
|------------|----------------------------|---------|
| SPEC-006-A | Installation Pipeline      | A       |

## Status History

| Date       | Status   | Changed By    | Notes                     |
|------------|----------|---------------|---------------------------|
| 2026-02-24 | Accepted | Chris Barlow  | Initial decision recorded |

## Governance

This ADR was authored following the WH(Y) decision format from [cgbarlow/adr](https://github.com/cgbarlow/adr). Changes to this decision require a new ADR that supersedes this one.
