# Example Scan Results

This page collects example scan outputs from di-test. These are point-in-time snapshots demonstrating what the tool produces.

---

## FinCap — Visual Pattern Scan

A visual pattern scan was run against the [FinCap Our Team page](https://www.fincap.org.nz/our-team/) as a proof of concept.

**Key findings:** 19 heading-like candidates (team member names using `<p class="h3">` instead of `<h3>`), 19 card-like candidates (repeated `<article>` structures), a link mismatch, and an empty `<h2>`.

| File | Description |
|------|-------------|
| [Scan Report (Markdown)](../output/accessibility-scan-report.md) | Detailed findings with analysis and recommendations |
| [Scan Report (Word)](../output/accessibility-scan-report.docx) | Same report in .docx format |
| [Findings JSON](../output/findings.json) | Structured JSON output with all 38 findings |
| [Full Page Screenshot](../output/screenshots/our-team-full.png) | Full-page capture |
| [Highlighted Screenshot](../output/screenshots/our-team-highlighted.png) | Red overlays on flagged elements |

### Sample Finding (JSON)

```json
{
  "url": "https://www.fincap.org.nz/our-team/",
  "type": "Heading-like content",
  "reason": "This appears to function as a heading but is not marked up as one. The element uses a <p> tag with class 'h3' and has visual characteristics of a heading: larger font size (30px vs 18px body), heavier weight (500 vs 400), isolated on its own line, with vertical margin separation.",
  "location": {
    "cssSelector": "section:nth-of-type(2) article:nth-child(1) p.h3.card-title",
    "xpath": "/html/body/main/section[2]/div/div[2]/div[1]/article/div[2]/p[1]"
  },
  "visual": { "fontSize": "30px", "fontWeight": "500" },
  "screenshot": "our-team-item0.png",
  "htmlSnippet": "<p class=\"h3 card-title mb-4\">Fleur Howard</p>",
  "confidence": 0.95
}
```

---

## MSD (Ministry of Social Development) — CWAC Scan

A CWAC scan was run against [msd.govt.nz](https://msd.govt.nz) on 2026-02-24, crawling 50 pages with axe-core, language, and reflow audits enabled.

| Metric | Value |
|--------|-------|
| Pages scanned | 50 |
| Axe-core issues | 27 (3 critical, 24 serious) |
| Language audit | All pages analysed (Flesch-Kincaid grade levels recorded) |
| Reflow audit | 0 overflow issues |

### Top Axe-core Findings

| Impact | Rule | Description | Count |
|--------|------|-------------|-------|
| Critical | `image-alt` | `<img>` elements missing alternative text | 3 |
| Serious | `list` | Lists not structured correctly | 24 |

### Scan Result Files

| File | Description |
|------|-------------|
| [Axe-Core Audit](../output/msd-govt-nz-2026-02-24/axe_core_audit.csv) | All axe-core findings across 50 pages |
| [Language Audit](../output/msd-govt-nz-2026-02-24/language_audit.csv) | Flesch-Kincaid and SMOG readability scores |
| [Reflow Audit](../output/msd-govt-nz-2026-02-24/reflow_audit.csv) | Horizontal overflow checks at 320px |
| [Pages Scanned](../output/msd-govt-nz-2026-02-24/pages_scanned.csv) | List of all 50 pages crawled |
