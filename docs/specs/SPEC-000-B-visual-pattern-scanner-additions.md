# SPEC-000-B: Visual Pattern Scanner — Additional Checks

| Field       | Value                                              |
|-------------|----------------------------------------------------|
| **ID**      | SPEC-000-B                                         |
| **ADR**     | ADR-000                                            |
| **Version** | B                                                  |
| **Status**  | Draft                                              |
| **Date**    | 2026-03-06                                         |
| **Author**  | Chris Barlow                                       |

## 1. Purpose

This specification extends SPEC-000-A by adding 10 new check categories to the visual pattern scanner. These checks are derived from the "Website checks group 2" document and cover government identity, CAPTCHA, carousels, disclosure widgets, heading text quality, link quality, skip links, modals, page titles, and print stylesheets.

All checks follow the same design principles as SPEC-000-A: the scanner flags patterns for human review, never auto-fails WCAG, and uses Playwright MCP for browser automation with Gherkin test scenarios defining detection logic.

## 2. Check Categories

### 2.1 Government Identity

Detect the presence of government identity elements: official logos/branding, contact information, copyright notices, and privacy policy links. References NZ Government Web Standards guidance on identity requirements.

### 2.2 CAPTCHA Detection

Detect CAPTCHA implementations on the page (reCAPTCHA, hCaptcha, image-based challenges, custom CAPTCHAs) and flag them for accessibility review. CAPTCHAs are a known barrier for users with disabilities.

### 2.3 Carousel Detection

Detect carousel/slider components and check whether they include a pause/stop mechanism. Auto-playing carousels without pause controls fail WCAG 2.2.2 (Pause, Stop, Hide).

### 2.4 Disclosure and Accordion Detection

Detect disclosure widgets (show/hide toggles) and accordion patterns. Check for proper use of `<details>`/`<summary>`, `aria-expanded`, and `aria-controls` attributes.

### 2.5 Heading Text Quality

Evaluate the quality of heading text content. Flag headings that are too long, too vague (e.g., "Click here", "Read more"), duplicated, or that skip hierarchy levels.

### 2.6 Link Quality

Check links for best practice: descriptive link text (not "click here" or "read more"), correct use of `aria-label`/`aria-labelledby`, links that open in new windows without warning, and adjacent duplicate links.

### 2.7 Skip Link Detection

Detect the presence and functionality of skip navigation links. Check that skip links are the first focusable element and that their target exists on the page.

### 2.8 Modal Dialog Detection

Detect modal/dialog patterns and check for proper implementation: use of `<dialog>` element or `role="dialog"`, focus trapping, close mechanism, and `aria-modal` attribute.

### 2.9 Page Title Check

Check that the page has a meaningful `<title>` element. Flag pages with missing titles, generic titles (e.g., "Untitled", "Home"), or titles that don't describe the page content.

### 2.10 Print Stylesheet Reminder

Flag pages as a reminder to check print stylesheets. This is a manual check reminder — the scanner notes the presence or absence of `@media print` styles.

## 3. Output Format Extension

Each new check category produces findings using the same JSON structure as SPEC-000-A, with the following additional type values:

| Type value                    | Check category |
|-------------------------------|----------------|
| Government identity           | 2.1            |
| CAPTCHA detected              | 2.2            |
| Carousel detected             | 2.3            |
| Disclosure widget detected    | 2.4            |
| Heading text quality          | 2.5            |
| Link quality                  | 2.6            |
| Skip link                     | 2.7            |
| Modal dialog detected         | 2.8            |
| Page title                    | 2.9            |
| Print stylesheet reminder     | 2.10           |

## 4. References

- [NZ Government Web Standards](https://www.digital.govt.nz/standards-and-guidance/nz-government-web-standards/)
- [WCAG 2.1 — Pause, Stop, Hide (2.2.2)](https://www.w3.org/WAI/WCAG21/Understanding/pause-stop-hide.html)
- [WCAG 2.1 — Link Purpose (2.4.4)](https://www.w3.org/WAI/WCAG21/Understanding/link-purpose-in-context.html)
- [WCAG 2.1 — Bypass Blocks (2.4.1)](https://www.w3.org/WAI/WCAG21/Understanding/bypass-blocks.html)
- [WCAG 2.1 — Page Titled (2.4.2)](https://www.w3.org/WAI/WCAG21/Understanding/page-titled.html)

## 5. Governance

This specification extends SPEC-000-A under ADR-000. Changes require a new version (SPEC-000-C).
