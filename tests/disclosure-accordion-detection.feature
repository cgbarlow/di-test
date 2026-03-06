Feature: Disclosure and Accordion Detection
  As an accessibility auditor
  I want to detect disclosure widgets and accordion patterns on a webpage
  So I can check whether they use proper semantic markup and ARIA attributes

  Background:
    Given I navigate to "<url>"

  Scenario: Detect native disclosure widgets
    When I scan the page for disclosure elements
    Then I should look for:
      | element                    | description                              |
      | <details>/<summary>        | native HTML disclosure widgets           |
      | [aria-expanded]            | elements with ARIA expanded state        |
      | [aria-controls]            | elements controlling another element     |
    And each detected disclosure should be flagged as "Disclosure widget detected"
    And the finding should note whether native HTML or ARIA is used

  Scenario: Detect accordion patterns
    When I scan the page for accordion-like patterns
    Then I should look for:
      | indicator                              | description                          |
      | repeated heading + collapsible content | heading-triggered show/hide groups   |
      | elements with "accordion" in class/id  | named accordion containers           |
      | multiple [aria-expanded] in sequence   | ARIA-based accordion pattern         |
    And groups of disclosure widgets in sequence should be flagged as an accordion pattern

  Scenario: Disclosure findings include implementation details
    When a disclosure widget is detected
    Then the finding should be labelled with type "Disclosure widget detected"
    And the reason should note:
      | detail                                 |
      | whether <details>/<summary> is used    |
      | whether aria-expanded is present       |
      | whether aria-controls points to a valid target |
    And the output should not state that the widget fails WCAG
