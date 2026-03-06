Feature: Modal Dialog Detection
  As an accessibility auditor
  I want to detect modal dialog patterns on a webpage
  So I can check whether they are implemented accessibly

  Background:
    Given I navigate to "<url>"

  Scenario: Detect native dialog elements
    When I scan the page for dialog elements
    Then I should look for:
      | element                    | description                              |
      | <dialog>                   | native HTML dialog element               |
      | [role="dialog"]            | ARIA dialog role                         |
      | [role="alertdialog"]       | ARIA alert dialog role                   |
    And each detected dialog should be flagged as "Modal dialog detected"

  Scenario: Detect modal-like overlay patterns
    When I scan the page for modal-like patterns
    Then I should look for:
      | indicator                              | description                          |
      | elements with "modal" in class/id      | named modal containers               |
      | elements with "dialog" in class/id     | named dialog containers              |
      | elements with "overlay" in class/id    | overlay containers that may be modals |
      | fixed/absolute positioned elements with high z-index | visual overlay patterns |
    And elements matching modal patterns should be flagged as "Modal dialog detected"

  Scenario: Check modal implementation attributes
    When a modal dialog is detected
    Then I should check for proper implementation:
      | attribute                  | description                              |
      | aria-modal="true"          | indicates modal behaviour to assistive tech |
      | aria-label or aria-labelledby | dialog has an accessible name          |
      | a close button or mechanism | user can dismiss the dialog             |
    And the reason should note which attributes are present or missing

  Scenario: Modal findings are flagged as patterns not violations
    When modal patterns are detected
    Then each finding should be labelled with type "Modal dialog detected"
    And the output should not state that the modal fails WCAG
    And the reason should describe the implementation pattern found and what to review
