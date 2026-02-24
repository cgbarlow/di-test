Feature: Screenshot and Highlighting
  As an accessibility auditor
  I want screenshots with highlighted regions for each finding
  So I can visually verify issues and provide audit evidence

  Background:
    Given I navigate to "https://www.fincap.org.nz/our-team/"
    And the tool has detected at least one heading-like or card-like element

  Scenario: Capture full-page screenshot for each flagged element
    When a heading-like or card-like element is flagged
    Then a full-page screenshot should be taken
    And the screenshot should be saved to the output directory

  Scenario: Draw a rectangle overlay highlighting the flagged element
    When a heading-like or card-like element is flagged
    Then the element's bounding box should be obtained
    And a visible rectangle overlay should be drawn around the element on the screenshot
    And the rectangle should be clearly distinguishable from the page content

  Scenario: Capture cropped screenshot of the flagged element
    When a heading-like or card-like element is flagged
    Then a cropped screenshot of the element and its immediate surroundings should be saved
    And the cropped image should include enough context to understand the element's placement

  Scenario: Store screenshot metadata for each finding
    When a screenshot is captured for a flagged element
    Then the following metadata should be stored:
      | field            | description                               |
      | screenshotPath   | file path to the full screenshot          |
      | croppedPath      | file path to the cropped screenshot       |
      | cssSelector      | the CSS selector of the element           |
      | pixelCoordinates | x, y, width, height of the bounding box   |

  Scenario: Screenshots should be usable for QA review
    When screenshots are generated
    Then each screenshot should clearly show which element was flagged
    And the file naming convention should include the page and item index (e.g. "our-team-item3.png")
