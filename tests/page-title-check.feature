Feature: Page Title Check
  As an accessibility auditor
  I want to check the page title for quality and presence
  So I can flag pages with missing, generic, or unhelpful titles

  Background:
    Given I navigate to "<url>"

  Scenario: Detect missing page title
    When I check the page for a <title> element
    Then if no <title> element exists, flag as "Page title" with reason "No page title found"
    And if the <title> element is empty, flag as "Page title" with reason "Page title is empty"

  Scenario: Detect generic or non-descriptive page titles
    When I check the page title content
    Then I should flag titles that are generic or non-descriptive such as:
      | generic title examples    |
      | "Untitled"                |
      | "Home"                    |
      | "Page"                    |
      | "Welcome"                 |
      | "Document"                |
      | the domain name only      |
    And each flagged title should have type "Page title"
    And the reason should explain that page titles should uniquely describe the page content

  Scenario: Report page title details
    When the page has a <title> element with content
    Then the finding should include the full title text
    And the finding should note the title length
    And the finding should be labelled with type "Page title"
    And the reason should confirm the title was found and provide the text for review
