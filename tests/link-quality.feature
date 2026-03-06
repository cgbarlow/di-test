Feature: Link Quality
  As an accessibility auditor
  I want to check links for accessibility best practices
  So I can flag links with poor text, missing ARIA, or problematic behaviour

  Background:
    Given I navigate to "<url>"

  Scenario: Detect non-descriptive link text
    When I scan all link elements on the page
    Then I should flag links with non-descriptive text such as:
      | non-descriptive text    |
      | "click here"            |
      | "here"                  |
      | "read more"             |
      | "more"                  |
      | "link"                  |
      | "download"              |
    And each flagged link should have type "Link quality"
    And the reason should explain that link text should describe the destination or purpose

  Scenario: Detect links that open in a new window without warning
    When I scan all link elements on the page
    Then I should identify links with target="_blank" or equivalent
    And I should check whether the link text or an aria-label indicates it opens in a new window
    And links opening in a new window without warning should be flagged with type "Link quality"
    And the reason should note that users should be warned when a link opens a new window

  Scenario: Detect adjacent duplicate links
    When I scan all link elements on the page
    Then I should identify adjacent links that point to the same URL (e.g., an image link followed by a text link to the same destination)
    And adjacent duplicate links should be flagged with type "Link quality"
    And the reason should suggest combining the links into a single link element

  Scenario: Check aria-label consistency on links
    When I scan link elements that have an aria-label attribute
    Then I should compare the aria-label text with the visible link text
    And if the aria-label does not contain the visible text, flag with type "Link quality"
    And the reason should explain that aria-label should include the visible text per WCAG 2.5.3

  Scenario: Detect empty links
    When I scan all link elements on the page
    Then I should flag links that have no visible text content and no aria-label
    And empty links should be flagged with type "Link quality"
    And the reason should explain that links must have an accessible name
