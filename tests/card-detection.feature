Feature: Card Detection
  As an accessibility auditor
  I want to detect card-like content structures on a webpage
  So I can flag content groups that may need accessibility review

  Background:
    Given I navigate to "https://www.fincap.org.nz/our-team/"

  # --- Structure-based card detection ---

  Scenario: Detect link-wrapped content groups containing image, heading, and text
    When I scan the page for anchor elements that wrap multiple child elements
    Then I should find groups where a single link contains:
      | element          | description                                      |
      | image            | an <img> tag or element with background-image     |
      | heading or title | a heading tag or heading-like text                |
      | body text        | additional descriptive text                       |
    And each group should be flagged as a "Card-like content" candidate

  Scenario: Detect cards using background-image instead of img tags
    When I scan the page for card candidates
    Then elements with CSS background-image should be treated the same as <img> tags
    And card candidates using background-image should be included in the results

  Scenario: Detect cards where multiple elements share the same link destination
    When I scan the page for groups of elements
    Then I should identify cases where multiple elements (image, heading, text) link to the same URL
    And even if they are not wrapped in a single <a> tag, they should be flagged as card candidates
    And the shared link destination should be recorded

  Scenario: Detect cards within a shared parent container
    When I scan the page for card candidates
    Then I should check if the image, heading, and text share a common parent container
    And groups within the same parent should strengthen the card candidate confidence

  Scenario: Detect repeated card patterns across the page
    When I scan the page for card candidates
    Then I should identify groups of similar card structures that repeat on the page
    And the number of repeated instances should be recorded
    And the common pattern (shared CSS classes, similar DOM structure) should be described

  Scenario: Detect vertical alignment in card candidates
    When I examine card candidate elements
    Then I should check if the image, heading, and text are vertically aligned
    And bounding boxes that align vertically should strengthen the card candidate confidence

  Scenario: Detect bounding box overlap in card candidates
    When I examine card candidate elements
    Then I should check if the bounding boxes of image, heading, and text overlap or are adjacent
    And elements with overlapping or adjacent bounding boxes should strengthen card confidence

  # --- Card output requirements ---

  Scenario: Card candidates should be reported as candidates not violations
    When card candidates are detected
    Then each should be labelled as "Card-like content" with type "candidate"
    And the output should not label any card as a WCAG violation or failure
    And the reason should explain the structural pattern found
