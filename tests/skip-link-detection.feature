Feature: Skip Link Detection
  As an accessibility auditor
  I want to detect skip navigation links on a webpage
  So I can verify they exist and function correctly for keyboard users

  Background:
    Given I navigate to "<url>"

  Scenario: Detect presence of skip link
    When I scan the page for skip navigation links
    Then I should look for:
      | indicator                                | description                          |
      | links with text containing "skip"        | e.g., "Skip to content", "Skip to main" |
      | links with href starting with "#"        | in-page anchor links near page start |
      | the first focusable element on the page  | skip links should be first           |
    And if a skip link is found, flag as "Skip link" with details of its text and target
    And if no skip link is found, flag as "Skip link" with reason "No skip navigation link detected"

  Scenario: Verify skip link target exists
    When a skip link is detected with an href pointing to an anchor (e.g., "#main-content")
    Then I should verify that the target element exists on the page
    And if the target does not exist, the reason should note "Skip link target not found on page"
    And if the target exists, the reason should confirm the target element and its tag

  Scenario: Check skip link position
    When a skip link is detected
    Then I should check whether it is one of the first focusable elements on the page
    And if the skip link is not among the first 3 focusable elements, flag with reason "Skip link is not among the first focusable elements"
    And the finding should note the skip link's position in the tab order
