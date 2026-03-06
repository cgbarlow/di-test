Feature: Carousel Detection
  As an accessibility auditor
  I want to detect carousel and slider components on a webpage
  So I can check whether they include pause controls and are accessible

  Background:
    Given I navigate to "<url>"

  Scenario: Detect carousel or slider components
    When I scan the page for carousel-like patterns
    Then I should look for:
      | indicator                              | description                          |
      | elements with "carousel" in class/id   | named carousel containers            |
      | elements with "slider" in class/id     | named slider containers              |
      | elements with "swiper" in class/id     | Swiper.js components                 |
      | elements with "slick" in class/id      | Slick carousel components            |
      | elements with role="region" containing multiple panels | ARIA carousel pattern |
    And each detected carousel should be flagged as "Carousel detected"

  Scenario: Check for auto-playing behaviour
    When a carousel component is detected
    Then I should check for indicators of auto-play:
      | indicator                              | description                          |
      | data-autoplay or data-auto-play        | autoplay data attributes             |
      | setInterval or setTimeout in scripts   | timer-based slide transitions        |
      | CSS animations on slide containers     | CSS-driven auto-rotation             |
    And if auto-play indicators are found, the reason should note this

  Scenario: Check for pause or stop controls
    When a carousel with auto-play indicators is detected
    Then I should look for pause/stop controls:
      | indicator                              | description                          |
      | button with "pause" text or aria-label | explicit pause button                |
      | button with "stop" text or aria-label  | explicit stop button                 |
      | play/pause toggle controls             | combined play/pause button           |
    And if no pause control is found, the reason should state "No pause/stop control detected — may not meet WCAG 2.2.2"

  Scenario: Carousel findings are flagged as patterns not violations
    When carousel patterns are detected
    Then each finding should be labelled with type "Carousel detected"
    And the output should not auto-fail WCAG
    And the reason should explain what was found and what to review
