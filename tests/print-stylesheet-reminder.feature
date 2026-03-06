Feature: Print Stylesheet Reminder
  As an accessibility auditor
  I want to be reminded to check print stylesheets
  So I can verify the page is usable when printed

  Background:
    Given I navigate to "<url>"

  Scenario: Check for print stylesheet presence
    When I scan the page for print-related styles
    Then I should look for:
      | indicator                                | description                          |
      | <link> with media="print"                | external print stylesheet            |
      | @media print blocks in inline styles     | embedded print styles                |
      | @media print in linked stylesheets       | print rules in main stylesheets      |
    And flag as "Print stylesheet reminder" with details of what was found
    And if no print styles are detected, the reason should state "No print stylesheet detected — manual print check recommended"
    And if print styles are found, the reason should state "Print styles detected — verify print output is usable"
