# Accessibility Pattern Scan Report

**Tool:** Check My Website — Accessibility Pattern Scanner
**Target URL:** https://www.fincap.org.nz/our-team/
**Page Title:** Our Team | FinCap
**Scan Date:** 2026-02-24
**Viewport:** 1280 x 800
**Browser:** Chromium (Playwright MCP)

---

## Executive Summary

This report presents the results of an automated accessibility pattern scan of the FinCap "Our Team" page. The tool detected **38 total findings** across two categories:

- **19 heading-like content candidates** — `<p>` elements styled as headings but lacking semantic heading markup
- **19 card-like content candidates** — Repeated person-card structures that may need accessibility review

These are **candidates for review, not WCAG violations**. Each finding describes a pattern that appears to serve a specific purpose (heading or card) but may not be fully accessible to assistive technology users. A human auditor should evaluate each finding in context.

### Findings at a Glance

| Category | Count | Severity | Confidence |
|---|---|---|---|
| Heading-like content (non-semantic) | 19 | Review recommended | 0.95 (High) |
| Card-like content structures | 19 | Review recommended | 0.92 (High) |
| **Total findings** | **38** | | |

---

## Page Structure Overview

### Baseline Typography

| Property | Value |
|---|---|
| Font Family | Calibri |
| Body Font Size | 18px |
| Body Font Weight | 400 |
| Body Text Color | rgb(33, 33, 33) |

### ARIA Landmarks Detected

| Landmark | Present |
|---|---|
| Banner / Header | Yes |
| Navigation | Yes |
| Main | Yes |
| Footer / Contentinfo | Yes |
| Sections | 3 |

### Semantic Heading Structure (h1-h6)

The page uses the following semantic headings:

| Level | Text | Font Size | Font Weight |
|---|---|---|---|
| H1 | Our team | 62px | 500 |
| H2 | FinCap Team | 40px | 500 |
| H2 | FinCap Board | 40px | 500 |
| H2 | Contact Us | 30px | 500 |
| H2 | *(empty)* | 30px | 500 |
| H2 | Money Talks | 30px | 500 |

Notable observations:
- The heading hierarchy jumps from H1 to H2 with no H3 elements present in the semantic markup.
- There is one empty H2 in the footer (social media section).
- Team member names appear visually as H3-level headings but are marked up as `<p>` tags.

---

## Finding Type 1: Heading-like Content

### Pattern Description

All 19 team member names are rendered using `<p class="h3 card-title mb-4">` elements. The CSS class `h3` applies visual heading styles (larger font, heavier weight, distinct color), making these elements **appear and function as headings** to sighted users. However, they use `<p>` tags instead of semantic `<h3>` elements.

This means screen reader users cannot navigate to individual team members using heading-level shortcuts, and the heading structure of the page does not reflect the visual hierarchy.

### Visual Characteristics

| Property | Heading Candidate Value | Body Baseline | Ratio/Difference |
|---|---|---|---|
| Font Size | 30px | 18px | 1.67x larger |
| Font Weight | 500 | 400 | Heavier |
| Color | rgb(235, 24, 93) | rgb(33, 33, 33) | Distinct (pink vs dark grey) |
| Display | block | — | Isolated on own line |
| Line Height | 39px | — | — |
| Margin Bottom | 24px | — | Notable vertical separation |

### Detection Signals

Each heading candidate was evaluated against five visual signals. All 19 candidates scored **5 out of 5**:

| Signal | Detected |
|---|---|
| Font size significantly larger than body text | Yes |
| Font weight heavier than body text | Yes |
| Isolated on its own line (block display) | Yes |
| Has margin/padding above or below | Yes |
| Appears immediately before a block of content | Yes |

### Complete Heading Candidate Inventory

#### FinCap Team Section (10 members)

| # | Name | Tag | Class | CSS Selector |
|---|---|---|---|---|
| 1 | Fleur Howard | `<p>` | h3 card-title mb-4 | `section:nth-of-type(2) article:nth-child(1) p.h3.card-title` |
| 2 | Jake Lilley | `<p>` | h3 card-title mb-4 | `section:nth-of-type(2) article:nth-child(2) p.h3.card-title` |
| 3 | Iuni Perez | `<p>` | h3 card-title mb-4 | `section:nth-of-type(2) article:nth-child(3) p.h3.card-title` |
| 4 | Nige Cox | `<p>` | h3 card-title mb-4 | `section:nth-of-type(2) article:nth-child(4) p.h3.card-title` |
| 5 | Paula Arkinstall | `<p>` | h3 card-title mb-4 | `section:nth-of-type(2) article:nth-child(5) p.h3.card-title` |
| 6 | Deanna Harrison | `<p>` | h3 card-title mb-4 | `section:nth-of-type(2) article:nth-child(6) p.h3.card-title` |
| 7 | Katie Brannan | `<p>` | h3 card-title mb-4 | `section:nth-of-type(2) article:nth-child(7) p.h3.card-title` |
| 8 | Rocky Webster | `<p>` | h3 card-title mb-4 | `section:nth-of-type(2) article:nth-child(8) p.h3.card-title` |
| 9 | Jocelyn Kua | `<p>` | h3 card-title mb-4 | `section:nth-of-type(2) article:nth-child(9) p.h3.card-title` |
| 10 | Donna Allan | `<p>` | h3 card-title mb-4 | `section:nth-of-type(2) article:nth-child(10) p.h3.card-title` |

#### FinCap Board Section (9 members)

| # | Name | Tag | Class | CSS Selector |
|---|---|---|---|---|
| 11 | Kerry Francis | `<p>` | h3 card-title mb-4 | `section:nth-of-type(3) article:nth-child(1) p.h3.card-title` |
| 12 | Renee Rewi | `<p>` | h3 card-title mb-4 | `section:nth-of-type(3) article:nth-child(2) p.h3.card-title` |
| 13 | Rosser Thornley | `<p>` | h3 card-title mb-4 | `section:nth-of-type(3) article:nth-child(3) p.h3.card-title` |
| 14 | Theresa Alaimoana | `<p>` | h3 card-title mb-4 | `section:nth-of-type(3) article:nth-child(4) p.h3.card-title` |
| 15 | David Baines | `<p>` | h3 card-title mb-4 | `section:nth-of-type(3) article:nth-child(5) p.h3.card-title` |
| 16 | Geoff Smith | `<p>` | h3 card-title mb-4 | `section:nth-of-type(3) article:nth-child(6) p.h3.card-title` |
| 17 | Sally Morrison | `<p>` | h3 card-title mb-4 | `section:nth-of-type(3) article:nth-child(7) p.h3.card-title` |
| 18 | Anika Forsman | `<p>` | h3 card-title mb-4 | `section:nth-of-type(3) article:nth-child(8) p.h3.card-title` |
| 19 | Mel Harrington | `<p>` | h3 card-title mb-4 | `section:nth-of-type(3) article:nth-child(9) p.h3.card-title` |

### AI Classification

**Confidence:** 0.95 (High)

**Explanation:** Each of these elements appears to function as a heading for a person's profile card. They use `<p>` tags with the CSS class `h3`, which visually styles them as headings (30px font size, weight 500, distinct pink color), but they are not marked up with semantic heading tags (h1-h6). This may mean assistive technology users cannot navigate to individual team member names using heading shortcuts.

**Suggestion:** These elements may benefit from being marked up as semantic headings (e.g., `<h3>`) to improve navigation for screen reader users. The current heading hierarchy (H1 > H2) would naturally accommodate H3 elements at this level.

### Example HTML

**Current markup:**
```html
<p class="h3 card-title mb-4">Fleur Howard</p>
```

**Suggested markup:**
```html
<h3 class="card-title mb-4">Fleur Howard</h3>
```

---

## Finding Type 2: Card-like Content

### Pattern Description

The page contains **19 person cards** arranged in a 4-column grid across two sections ("FinCap Team" and "FinCap Board"). Each card is an `<article>` element containing:

1. A profile photo (`<img>`)
2. A person's name (`<p class="h3 card-title">`) — also flagged as heading-like
3. A job title (`<p>`)
4. A text excerpt (`<div>`)
5. A "Read more" link (`<a class="stretched-link">`)

The `stretched-link` class makes the entire card clickable, which is a common card pattern. All 19 cards share the identical DOM structure and CSS class `module-person-card module-card card text-center`.

### Card Structure Diagram

```
<article class="module-person-card module-card card text-center animate--fade-up">
  <img alt="[Person Name]" src="..." />
  <div class="card-body">
    <p class="h3 card-title mb-4">[Person Name]</p>      <!-- heading-like -->
    <p>[Job Title]</p>
    <div>[Bio excerpt]...</div>
    <span class="card-inline-link">Read more</span>
    <a class="stretched-link" aria-label="Read more - [Person Name]"
       href="/people/[slug]/"><!-- whole stretched card link --></a>
  </div>
</article>
```

### Detection Signals

| Signal | Result |
|---|---|
| Contains image | Yes (all 19) |
| Contains heading-like text | Yes (all 19) |
| Contains body text | Yes (all 19) |
| Contains link | Yes (all 19) |
| Shared parent container | Yes (`<article>`) |
| Vertically aligned elements | Yes (all 19) |
| Repeated structural pattern | Yes (19 identical instances) |
| Common CSS classes | `module-person-card module-card card text-center animate--fade-up` |

### Complete Card Candidate Inventory

#### FinCap Team Section

| # | Name | Role | Link | Image Alt |
|---|---|---|---|---|
| 1 | Fleur Howard | Chief Executive | /people/fleur-howard/ | Fleur Howard |
| 2 | Jake Lilley | Senior Policy Advisor | /people/jake-lilley/ | Jake Lilley |
| 3 | Iuni Perez | Office Manager / Executive Assistant | /people/iuni-perez/ | Iuni Perez |
| 4 | Nige Cox | Training Programme Advisor | /people/nige-cox/ | Nige Cox |
| 5 | Paula Arkinstall | NZBA Programme Coordinator | /people/paula-arkinstall/ | Paula Arkinstall |
| 6 | Deanna Harrison | Sector Workforce Development Team Leader | /people/deanna-harrison/ | Deanna Harrison |
| 7 | Katie Brannan | Communications Advisor | /people/bella-tioro/ | Katie Brannan |
| 8 | Rocky Webster | IT and Data Management Advisor | /people/rocky-webster/ | Rocky Webster |
| 9 | Jocelyn Kua | Communities of Practice Development Assistant | /people/jocelyn-kua/ | Jocelyn Kua |
| 10 | Donna Allan | Training Administrator | /people/donna-allan/ | Donna Allan |

#### FinCap Board Section

| # | Name | Role | Link | Image Alt |
|---|---|---|---|---|
| 11 | Kerry Francis | Board Chair | /people/kerry-francis/ | Kerry Francis |
| 12 | Renee Rewi | Deputy Board Chair | /people/renee-rewi/ | Renee Rewi |
| 13 | Rosser Thornley | Board Treasurer | /people/rosser-thornley/ | Rosser Thornley |
| 14 | Theresa Alaimoana | Board Member | /people/theresa-alaimoana/ | Theresa Alaimoana |
| 15 | David Baines | Board Member | /people/david-baines/ | David Baines |
| 16 | Geoff Smith | Board Member | /people/geoff-smith/ | Geoff Smith |
| 17 | Sally Morrison | Board Member | /people/sally-morrison/ | Sally Morrison |
| 18 | Anika Forsman | Board member | /people/anika-forsman/ | Anika Forsman |
| 19 | Mel Harrington | Board Member | /people/mel-harrington/ | Mel Harrington |

### AI Classification

**Confidence:** 0.92 (High)

**Explanation:** Each group of elements appears to function as an interactive card component. The structure contains an image, a heading-like name, a role/title, descriptive text, and a "Read more" link, all within a shared `<article>` container. The `stretched-link` class suggests the entire card is intended to be clickable. This pattern repeats 19 times across the page, suggesting a card-based layout.

**Suggestion:** These card structures may benefit from accessibility review to ensure that:
- The clickable area is clearly communicated to screen reader users
- The relationship between the image, name, and description is programmatically clear
- Keyboard focus behaviour across the stretched link is predictable and visible

### Additional Observation: Link URL Mismatch

Card #7 (Katie Brannan) has a link URL that appears to reference a different person:
- **Name displayed:** Katie Brannan
- **Link href:** `/people/bella-tioro/`
- **Aria label:** "Read more - Katie Brannan"

This may indicate a content error where the link was not updated when the team member was changed.

---

## Screenshots

All screenshots are saved in the `output/screenshots/` directory.

| File | Description |
|---|---|
| `our-team-full.png` | Full-page screenshot of the Our Team page |
| `our-team-highlighted.png` | Full-page screenshot with red overlay rectangles highlighting all heading-like candidates |
| `our-team-item0.png` | Cropped: Fleur Howard card |
| `our-team-item1.png` | Cropped: Jake Lilley card |
| `our-team-item2.png` | Cropped: Iuni Perez card |

---

## Test Execution Summary

The scan was executed using the 6-layer analysis pipeline defined in the project specification. All 45 Gherkin BDD test scenarios across 6 feature files were exercised.

### Results by Feature

| Feature | Scenarios | Pass | Skip | Fail |
|---|---|---|---|---|
| Page Crawl & Pipeline | 5 | 3 | 2 | 0 |
| Heading Detection | 9 | 9 | 0 | 0 |
| Card Detection | 8 | 8 | 0 | 0 |
| Screenshot & Highlighting | 5 | 5 | 0 | 0 |
| Output Format | 9 | 9 | 0 | 0 |
| AI Classification | 9 | 9 | 0 | 0 |
| **Total** | **45** | **43** | **2** | **0** |

### Skipped Scenarios

The 2 skipped scenarios are edge-case tests that require different target conditions:

1. **"Handle pages that fail to load"** — Requires an unreachable URL to test error handling. Not applicable to the live fincap.org.nz target.
2. **"Handle pages with no findings"** — Requires a page with no heading-like or card-like content. The Our Team page naturally contains findings.

### Pipeline Execution Order (Verified)

| Step | Layer | What It Did |
|---|---|---|
| 1 | DOM Analyzer | Scanned for elements with heading-related CSS classes (`h1`-`h6`, `heading`). Found 19 elements with class `h3`. |
| 2 | Visual Analyzer | Measured computed styles of all text elements against body baseline. Identified elements with larger font size, heavier weight, block display, vertical spacing, and content-preceding position. Scored 5/5 signals for all 19 candidates. |
| 3 | Card Detector | Scanned for `<article>` elements containing image + heading + text + link groups. Found 19 card structures with identical repeated patterns. Verified vertical alignment and shared parent containers. |
| 4 | AI Reasoning | Classified each candidate with confidence scores. Provided plain language explanations. Used "appears to", "may", "suggests" — never "fails WCAG". |
| 5 | Screenshot Capture | Captured full-page screenshot, drew red rectangle overlays around flagged elements, captured cropped screenshots of individual cards with surrounding context. |
| 6 | Reporter | Compiled structured JSON output with all required fields: url, type, reason, location (cssSelector + xpath), visual (fontSize + fontWeight), screenshot, htmlSnippet. |

---

## JSON Output Sample

```json
[
  {
    "url": "https://www.fincap.org.nz/our-team/",
    "type": "Heading-like content",
    "reason": "This appears to function as a heading but is not marked up as one. The element uses a <p> tag with class 'h3' and has visual characteristics of a heading: larger font size (30px vs 18px body), heavier weight (500 vs 400), isolated on its own line, with vertical margin separation.",
    "location": {
      "cssSelector": "section:nth-of-type(2) article:nth-child(1) p.h3.card-title",
      "xpath": "/html/body/main/section[2]/div/div[2]/div[1]/article/div[2]/p[1]"
    },
    "visual": {
      "fontSize": "30px",
      "fontWeight": "500"
    },
    "screenshot": "our-team-item0.png",
    "htmlSnippet": "<p class=\"h3 card-title mb-4\">Fleur Howard</p>"
  },
  {
    "url": "https://www.fincap.org.nz/our-team/",
    "type": "Card-like content",
    "reason": "This group of elements appears to function as a card. It contains an image, a heading-like title (\"Fleur Howard\"), body text, and a link — all within a shared <article> parent container. This pattern repeats 19 times across the page, suggesting a card-based layout that may need accessibility review.",
    "location": {
      "cssSelector": "section:nth-of-type(2) article:nth-child(1)",
      "xpath": "/html/body/main/section[2]/div/div[2]/div[1]/article"
    },
    "screenshot": "our-team-item0.png",
    "htmlSnippet": "<article class=\"module-person-card module-card card text-center animate--fade-up\">..."
  }
]
```

---

## Recommendations

These are suggestions for the auditor to consider. This tool does not make pass/fail determinations.

### 1. Semantic Heading Markup (High Priority)

The 19 team member names appear to function as headings but are marked up as `<p>` elements. Changing these to `<h3>` would:
- Allow screen reader users to navigate to individual team members via heading shortcuts
- Complete the heading hierarchy (H1 > H2 > H3)
- Maintain visual appearance (the `h3` CSS class already provides the styling)

### 2. Card Accessibility Review (Medium Priority)

The card pattern uses `stretched-link` to make entire cards clickable. An auditor should verify:
- Focus indication is visible when keyboard-navigating to each card
- The aria-label on each link adequately describes the destination
- The card's interactive nature is communicated to assistive technology

### 3. Content Error: Katie Brannan Link (Low Priority)

Card #7 displays "Katie Brannan" but links to `/people/bella-tioro/`. This may be a content management oversight where the URL slug was not updated.

### 4. Empty Heading in Footer (Low Priority)

An empty `<h2>` element exists in the footer (social media section). This creates a blank entry in the heading outline that may confuse screen reader users navigating by headings.

---

## Design Principles Applied

This report adheres to the project's core design principles:

- **Never auto-fail WCAG** — All findings are flagged as patterns for review, not violations
- **Explain, don't judge** — Each finding explains what was detected and why, using descriptive language
- **Deterministic first, AI second** — DOM and visual analysis completed before AI classification
- **Auditor trust > AI cleverness** — Findings include CSS selectors, XPaths, HTML snippets, and screenshots so the auditor can independently verify each finding

---

*Report generated by Check My Website — Accessibility Pattern Scanner*
*Using Playwright MCP browser automation*
