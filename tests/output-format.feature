Feature: Output Format
  As an accessibility auditor
  I want structured JSON output for each finding
  So I can process, review, and integrate results into reports

  Background:
    Given I navigate to "https://www.fincap.org.nz/our-team/"
    And the tool has completed its scan

  Scenario: Each finding includes the page URL
    When the scan produces findings
    Then every finding in the JSON output should include a "url" field
    And the "url" should match the scanned page URL

  Scenario: Each finding includes a type classification
    When the scan produces findings
    Then every finding should include a "type" field
    And the type should be one of:
      | type                  |
      | Heading-like content  |
      | Card-like content     |

  Scenario: Each finding includes DOM location
    When the scan produces findings
    Then every finding should include a "location" object with:
      | field       | description                              |
      | cssSelector | a CSS selector that uniquely locates it  |
      | xpath       | an XPath expression that locates it      |

  Scenario: Each finding includes a screenshot reference
    When the scan produces findings
    Then every finding should include a "screenshot" field
    And the "screenshot" field should contain a valid file path to the saved screenshot

  Scenario: Each finding includes the HTML code snippet
    When the scan produces findings
    Then every finding should include an "htmlSnippet" field
    And the snippet should contain the element's outer HTML including its attributes

  Scenario: Each finding includes visual style data
    When the scan produces findings for heading-like content
    Then the finding should include a "visual" object with:
      | field      |
      | fontSize   |
      | fontWeight |

  Scenario: Each finding includes a reason for flagging
    When the scan produces findings
    Then every finding should include a "reason" field
    And the reason should explain in plain language why the element was flagged
    And the reason should never state that the element fails WCAG

  Scenario: Output is valid JSON
    When the scan completes
    Then the full output should be valid parseable JSON
    And it should be an array of finding objects

  Scenario: JSON output example structure matches spec
    When the scan produces a heading-like finding
    Then the JSON structure should match:
      """json
      {
        "url": "https://www.fincap.org.nz/our-team/",
        "type": "Heading-like content",
        "reason": "<plain language explanation>",
        "location": {
          "cssSelector": "<selector>",
          "xpath": "<xpath>"
        },
        "visual": {
          "fontSize": "<value>",
          "fontWeight": "<value>"
        },
        "screenshot": "<file path>",
        "htmlSnippet": "<outer HTML>"
      }
      """
