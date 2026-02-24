Feature: Heading Detection
  As an accessibility auditor
  I want to detect heading-like content on a webpage
  So I can flag elements that may need proper heading markup

  Background:
    Given I navigate to "https://www.fincap.org.nz/our-team/"

  # --- Class-based heading detection (DOM/rules-based) ---

  Scenario: Detect elements with heading class names
    When I scan the page for elements with class names containing "h1", "h2", "h3", "h4", "h5", or "h6"
    Then I should find at least one element with a heading-related class name
    And each detected element should record:
      | field       | description                          |
      | tagName     | the HTML tag name of the element     |
      | className   | the full class attribute value       |
      | ariaRole    | any ARIA role attribute              |
      | textContent | the visible text content             |
      | cssSelector | a unique CSS selector for the element|
      | xpath       | the XPath to the element             |

  Scenario: Class-based heading detection is case-insensitive
    When I scan the page for elements with class names containing heading indicators
    Then the scan should match class names regardless of case
    And classes like "H1", "h1", "heading1", "pageH2title" should all be detected

  Scenario: Record computed styles for class-based headings
    When I find elements with heading-related class names
    Then each element should record its computed styles:
      | style      |
      | fontSize   |
      | fontWeight |
      | color      |
    And the position in the DOM should be recorded

  # --- Visual heading detection (semi-AI) ---

  Scenario: Detect text that is visually larger than body text
    When I measure the computed font size of all visible text elements on the page
    Then I should identify text elements whose font size is significantly larger than the body text
    And those elements should be flagged as "Heading-like content"

  Scenario: Detect text that is visually heavier than body text
    When I measure the computed font weight of all visible text elements on the page
    Then I should identify text elements whose font weight is heavier than the body text (e.g. 700 or bold)
    And those elements should be flagged as "Heading-like content"

  Scenario: Detect text isolated on its own line
    When I examine text elements on the page
    Then I should identify text that is on its own line (block-level or has line breaks before and after)
    And that text is not inside a paragraph with other sentences
    And such text should be considered a heading candidate

  Scenario: Detect text with vertical margin separation
    When I examine text elements flagged as heading candidates
    Then I should check if they have margin or padding above and/or below
    And elements with notable vertical spacing should increase heading confidence

  Scenario: Detect text that appears before a block of content
    When I examine text elements flagged as heading candidates
    Then I should verify they appear immediately before a block of body content
    And elements that precede content blocks should increase heading confidence

  Scenario: Combine visual signals for heading-like detection
    When I scan the page for heading-like visual patterns
    Then elements meeting multiple criteria should be ranked higher:
      | criterion                           |
      | font size larger than body text     |
      | font weight heavier than body text  |
      | isolated on its own line            |
      | has margin/padding above or below   |
      | appears before a block of content   |
    And each flagged element should include a reason explaining why it was flagged

  # --- Heading elements not tagged as headings ---

  Scenario: Identify heading-like elements that are not semantic heading tags
    When I find elements that match heading visual or class-based patterns
    Then I should check if each element uses a semantic heading tag (h1-h6)
    And elements that look like headings but use div, span, p, or other non-heading tags should be flagged
    And the reason should state "This appears to function as a heading but is not marked up as one"
