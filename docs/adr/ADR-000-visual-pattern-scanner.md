# ADR-000: Visual Pattern Scanner

| Field    | Value                                        |
|----------|----------------------------------------------|
| **ID**   | ADR-000                                      |
| **Status** | Accepted                                   |
| **Date** | 2026-02-24                                   |
| **Author** | Chris Barlow                               |

## WH(Y) Decision Statement

**In the context of** needing to detect accessibility patterns that pass automated WCAG checks but may still confuse users,

**facing** the limitation that axe-core and similar tools only test programmatically-defined WCAG criteria and cannot identify elements that *look like* headings or cards without proper semantic markup,

**we decided for** an LLM-driven visual pattern scanner using Playwright MCP for browser automation with Gherkin test scenarios defining the detection pipeline,

**and neglected** extending CWAC with custom plugins, building a standalone headless browser tool, and purely rule-based static analysis,

**to achieve** detection of heading-like and card-like content patterns that complement CWAC's WCAG compliance scanning,

**accepting that** the scanner flags patterns rather than violations, AI classification adds variability, and the tool requires an LLM to execute test scenarios.

## Context

Automated accessibility testing tools like axe-core are effective at detecting WCAG violations that can be programmatically tested — missing alt text, insufficient colour contrast, missing form labels, etc. However, they cannot detect elements that *appear* to function as headings or navigational cards but lack the semantic markup to support assistive technology users.

For example, a `<p class="h3">Team Member Name</p>` looks like a heading to sighted users but is invisible to screen readers as a heading. Similarly, repeated content groups with images, text, and shared link destinations function as cards but may lack appropriate landmark or list structure.

These patterns require visual interpretation — understanding how elements *appear* on screen and how users would perceive their function. This is a task well-suited to LLM-driven analysis.

## Decision

We will build a visual pattern scanner that uses Playwright MCP for browser automation, with detection logic defined as Gherkin test scenarios. The LLM reads the test scenarios and executes each step via Playwright MCP tool calls, combining deterministic DOM analysis with AI-powered visual classification.

### Detection pipeline

1. **DOM Analyzer** — Class-based heading detection (deterministic)
2. **Visual Analyzer** — Heading-like visual patterns (rules-based)
3. **Card Detector** — Card candidate structure detection (heuristic)
4. **AI Reasoning** — Classification + plain language explanation
5. **Screenshot Capture** — Full-page + cropped + highlight overlays
6. **Reporter** — Structured JSON + report compilation

### What it detects

**Heading-like content:**
- Elements with class names containing h1–h6 (case-insensitive)
- Text visually styled as a heading (larger, bolder, isolated)
- Non-semantic tags (`<div>`, `<span>`, `<p>`) functioning as headings

**Card-like content:**
- Link-wrapped groups (image + heading + body text inside `<a>`)
- Shared destinations (multiple elements linking to the same URL)
- Repeated patterns (matching DOM structure and CSS classes)

## Rationale

### Why LLM-driven Playwright MCP over alternatives

**Alternative 1: Extend CWAC with custom plugins**

CWAC's plugin architecture could theoretically support custom visual checks, but:
- CWAC plugins operate on axe-core's DOM serialisation, not visual rendering.
- Adding screenshot and bounding-box analysis would require significant CWAC modifications, violating our zero-modification principle (ADR-002).
- Visual pattern detection requires spatial reasoning that axe-core's rule engine doesn't support.

**Alternative 2: Standalone headless browser tool**

Building a custom Puppeteer/Playwright script was considered:
- Would require maintaining a separate codebase with its own CLI and configuration.
- Loses the conversational interface — users would need to interpret raw JSON output.
- Cannot leverage LLM reasoning for ambiguous cases (is this *really* a heading?).

**Alternative 3: Purely rule-based static analysis**

Defining strict rules for heading-like and card-like detection:
- Brittle — every new CSS framework brings new class naming conventions.
- Cannot handle visual styling (a `<div>` with `font-size: 2rem; font-weight: 700` *looks* like a heading regardless of class name).
- No confidence scoring — everything is either a match or not.

**Why Playwright MCP + LLM wins:**

- Playwright MCP provides real browser rendering, computed styles, and screenshot capabilities.
- The LLM can reason about visual context — "this text is large, bold, isolated, and precedes a content block, so it functions as a heading."
- Gherkin scenarios make the detection logic readable, auditable, and extensible.
- The same Playwright MCP server is already configured for di-test, so no additional infrastructure is needed.
- Findings include explanations in plain language, making them useful for non-technical stakeholders.

## Consequences

### Positive

- Catches accessibility patterns that no automated tool can detect.
- Explanations help auditors understand *why* something was flagged.
- Gherkin scenarios serve as both test definitions and documentation.
- Complements CWAC scans — together they provide comprehensive coverage.

### Negative

- Requires an LLM to execute (cannot run as a standalone CLI tool).
- AI classification introduces variability between runs.
- Slower than automated scans — each page requires multiple Playwright interactions.
- Flags patterns, not violations — findings require human judgement.

## Dependencies

| Relationship  | Target   | Description                                            |
|---------------|----------|--------------------------------------------------------|
| RELATES_TO    | ADR-001  | CWAC MCP integration (complementary scanning approach) |

## Referenced Specification

| Spec ID    | Title                   | Version |
|------------|-------------------------|---------|
| SPEC-000-A | Visual Pattern Scanner  | A       |

## Status History

| Date       | Status   | Changed By    | Notes                     |
|------------|----------|---------------|---------------------------|
| 2026-02-24 | Accepted | Chris Barlow  | Initial decision recorded |

## Governance

This ADR was authored following the WH(Y) decision format from [cgbarlow/adr](https://github.com/cgbarlow/adr). Changes to this decision require a new ADR that supersedes this one.
