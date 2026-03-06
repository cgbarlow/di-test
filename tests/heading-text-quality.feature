Feature: Heading Text Quality
  As an accessibility auditor
  I want to evaluate the quality of heading text on a webpage
  So I can flag headings that are vague, too long, duplicated, or skip hierarchy levels

  Background:
    Given I navigate to "<url>"

  Scenario: Detect vague or generic heading text
    When I scan all heading elements (h1-h6) on the page
    Then I should flag headings with vague or non-descriptive text such as:
      | vague text examples     |
      | "Click here"            |
      | "Read more"             |
      | "Learn more"            |
      | "More information"      |
      | "Details"               |
      | "Link"                  |
      | untitled                |
    And each flagged heading should have type "Heading text quality"
    And the reason should explain that heading text should describe the content that follows

  Scenario: Detect headings that are excessively long
    When I scan all heading elements (h1-h6) on the page
    Then I should flag headings with text content longer than approximately 80 characters
    And the reason should explain that headings should be concise and scannable

  Scenario: Detect duplicate heading text
    When I scan all heading elements (h1-h6) on the page
    Then I should identify headings that share identical text content at the same level
    And duplicate headings should be flagged with type "Heading text quality"
    And the reason should note the number of duplicates and suggest differentiation

  Scenario: Detect heading hierarchy skips
    When I scan all heading elements (h1-h6) on the page
    Then I should check the heading hierarchy for level skips (e.g., h1 followed by h3 with no h2)
    And skipped levels should be flagged with type "Heading text quality"
    And the reason should explain the expected heading hierarchy
