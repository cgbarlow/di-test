Feature: Page Crawl and Analysis Pipeline
  As an accessibility auditor
  I want to crawl a single page and run the full analysis pipeline
  So I can get a complete set of accessibility findings

  Background:
    Given the target URL is "https://www.fincap.org.nz/our-team/"

  Scenario: Successfully load the target page
    When I navigate to the target URL
    Then the page should load without errors
    And the page title should be captured
    And the page URL should be recorded in all findings

  Scenario: Extract all text nodes with computed styles
    When the page has loaded
    Then I should extract all visible text nodes on the page
    And each text node should include its computed styles:
      | style      |
      | fontSize   |
      | fontWeight |
      | color      |
      | display    |
      | lineHeight |

  Scenario: Analysis pipeline runs in correct order
    When I run the full analysis on the page
    Then the layers should execute in this order:
      | order | layer              | description                          |
      | 1     | DOM Analyzer       | class-based heading detection        |
      | 2     | Visual Analyzer    | heading-like visual pattern detection|
      | 3     | Card Detector      | card candidate structure detection   |
      | 4     | AI Reasoning       | classification and explanation        |
      | 5     | Screenshot Capture | highlight and save screenshots        |
      | 6     | Reporter           | compile JSON output                   |

  Scenario: Handle pages that fail to load
    Given the target URL is an unreachable address
    When I attempt to navigate to the target URL
    Then the tool should report a clear error
    And the error should include the URL that failed

  Scenario: Handle pages with no findings
    Given the target page has no heading-like or card-like content
    When I run the full analysis
    Then the output should be an empty JSON array
    And no error should be thrown
