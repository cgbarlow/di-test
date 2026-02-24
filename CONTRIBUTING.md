# Contributing to di-test

Thanks for your interest in contributing to di-test.

## Feature Requests and Bug Reports

Please submit feature requests and bug reports on the [GitHub Issues page](https://github.com/cgbarlow/di-test/issues).

## Getting Started

For development setup instructions, see [Manual Setup](docs/MANUAL-SETUP.md).

For architecture, project structure, ADRs, and technical specifications, see [Architecture](docs/ARCHITECTURE.md).

## Running Tests

```bash
pytest tests/
```

The test suite includes 103 pytest tests across 9 test files covering environment detection, axe-core scanner, config builder, result reader, scan registry, report generation, templates, and plugin manifest.

## Documentation Conventions

- **ADRs** use the WH(Y) format (context, decision, rationale, consequences) in `docs/adr/`
- **SPECs** provide detailed implementation guidance in `docs/specs/`
- **Technical references** live in `docs/` (CWAC-MCP.md, VISUAL-SCANNER.md, ARCHITECTURE.md)
- **User-facing docs** live at the repo root (README.md, CONTRIBUTING.md)
