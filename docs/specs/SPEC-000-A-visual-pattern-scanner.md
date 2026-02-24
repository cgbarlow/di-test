# SPEC-000-A: Visual Pattern Scanner

| Field          | Value                                        |
|----------------|----------------------------------------------|
| **Parent ADR** | [ADR-000](../adr/ADR-000-visual-pattern-scanner.md) |
| **Version**    | A                                            |
| **Status**     | Accepted                                     |
| **Date**       | 2026-02-24                                   |

## Overview

This specification defines the visual pattern scanner — an LLM-driven accessibility analysis tool that detects elements which *look like* headings or cards but may lack proper semantic markup. It operates via Playwright MCP browser automation, with detection logic defined as Gherkin test scenarios.

The scanner flags patterns, not violations. It never auto-fails WCAG. All findings include plain language explanations and evidence (screenshots, selectors, HTML snippets) for human review.

## 1. Scope

The visual pattern scanner detects two categories of accessibility patterns:

1. **Heading-like content** — Elements that visually function as headings but are not marked up with `<h1>`–`<h6>` tags.
2. **Card-like content** — Groups of content that function as navigational cards but may lack appropriate semantic structure.

It is designed to complement CWAC's WCAG compliance scanning. CWAC finds violations that can be programmatically tested; the visual scanner catches patterns that require visual interpretation.

## 2. Detection Pipeline

The scanner executes a 6-layer analysis pipeline for each target page:

| Layer | Name | Method | Purpose |
|-------|------|--------|---------|
| 1 | DOM Analyzer | Deterministic | Class-based heading detection (h1–h6 in class names) |
| 2 | Visual Analyzer | Rules-based | Heading-like visual patterns (font size, weight, isolation) |
| 3 | Card Detector | Heuristic | Card candidate structure detection |
| 4 | AI Reasoning | LLM | Classification + plain language explanation |
| 5 | Screenshot Capture | Automated | Full-page + cropped + highlight overlays |
| 6 | Reporter | Automated | Structured JSON + report compilation |

### 2.1 DOM Analyzer (Layer 1)

Detects elements with class names containing heading identifiers:

- Matches: `h1`, `h2`, `h3`, `h4`, `h5`, `h6` (case-insensitive, partial match)
- Records: tag name, ARIA roles, font size, font weight, colour, DOM position

### 2.2 Visual Analyzer (Layer 2)

Flags text where:

- Font size is larger than surrounding body text
- Font weight is heavier than surrounding content
- Text is isolated on its own line
- Has margin above/below separating it from adjacent content
- Appears before a block of content (heading position)

### 2.3 Card Detector (Layer 3)

Identifies card candidates using structural heuristics:

- **Link-wrapped groups**: An `<a>` wrapping an image + heading + body text
- **Shared destinations**: Multiple elements linking to the same URL within a container
- **Repeated patterns**: Groups with matching DOM structure and CSS classes
- **Structural heuristics**: Shared parent containers, vertical alignment, bounding box adjacency

### 2.4 AI Reasoning (Layer 4)

The LLM receives:

- HTML snippet of the candidate element
- Computed styles (font size, weight, colour, margins)
- Screenshot crop of the element and surrounding context
- Surrounding DOM context

The LLM classifies:

- "Is this functioning as a heading?" / "Is this functioning as a card?"
- Provides a plain language explanation of *why* it was flagged
- Assigns a confidence score (0–1)
- Suggests what *might* be wrong (never auto-fails)

### 2.5 Screenshot Capture (Layer 5)

For each flagged element:

1. Get bounding box from Playwright
2. Take a full-page screenshot
3. Draw a rectangle overlay (red highlight) around the element
4. Save full screenshot and cropped screenshot

### 2.6 Reporter (Layer 6)

Produces structured output in JSON format, then renders to markdown and Word document.

## 3. Output Format

Each finding includes:

| Field | Type | Description |
|-------|------|-------------|
| `url` | string | URL of the scanned page |
| `type` | string | `"Heading-like content"` or `"Card-like content"` |
| `reason` | string | Plain language explanation of why it was flagged |
| `location.cssSelector` | string | CSS selector that uniquely locates the element |
| `location.xpath` | string | XPath expression that locates the element |
| `visual.fontSize` | string | Computed font size (heading-like only) |
| `visual.fontWeight` | string | Computed font weight (heading-like only) |
| `screenshot` | string | File path to the saved screenshot |
| `htmlSnippet` | string | The element's outer HTML including attributes |
| `confidence` | number | AI confidence score (0–1) |

## 4. Test Scenarios

Detection logic is defined as Gherkin test scenarios:

| File | Scenarios | Covers |
|------|-----------|--------|
| `page-crawl.feature` | 5 | Page load, text extraction, pipeline order, error handling |
| `heading-detection.feature` | 9 | Class-based and visual heading detection |
| `card-detection.feature` | 8 | Card structure detection and heuristics |
| `screenshot-and-highlighting.feature` | 5 | Screenshot capture, overlays, metadata |
| `output-format.feature` | 9 | JSON output structure and field validation |
| `ai-classification.feature` | 9 | AI input/output, confidence scoring, tone |

**45 scenarios total** — 43 pass, 2 skipped (edge-case conditions).

## 5. Design Principles

1. **Never auto-fail WCAG** — The tool flags patterns, not violations.
2. **Explain, don't judge** — Findings include plain language explanations.
3. **Deterministic first, AI second** — AI interprets what rules-based analysis found.
4. **Auditor trust > AI cleverness** — Findings include selectors, XPaths, HTML snippets, and screenshots.

## Related Specifications

| Spec ID    | Relationship | Description |
|------------|-------------|-------------|
| SPEC-001-A | Complements | MCP tool definitions for CWAC (complementary scanning approach) |

## Changelog

| Version | Date       | Author        | Changes                      |
|---------|------------|---------------|------------------------------|
| A       | 2026-02-24 | Chris Barlow  | Initial specification        |
