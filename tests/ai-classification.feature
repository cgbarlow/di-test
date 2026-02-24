Feature: AI Classification and Explanation
  As an accessibility auditor
  I want AI-powered classification and plain language explanations
  So I can understand findings without deep technical expertise

  Background:
    Given I navigate to "https://www.fincap.org.nz/our-team/"
    And the DOM and visual analysis layers have produced candidates

  # --- AI input requirements ---

  Scenario: AI receives the HTML snippet for each candidate
    When a candidate is sent to the AI reasoning layer
    Then the AI should receive the element's HTML snippet
    And the snippet should include the element and its surrounding DOM context

  Scenario: AI receives computed styles for each candidate
    When a candidate is sent to the AI reasoning layer
    Then the AI should receive the element's computed styles
    Including font size, font weight, color, and display properties

  Scenario: AI receives a screenshot crop for each candidate
    When a candidate is sent to the AI reasoning layer
    Then the AI should receive a cropped screenshot of the element
    And the crop should include enough surrounding context

  Scenario: AI receives surrounding DOM context
    When a candidate is sent to the AI reasoning layer
    Then the AI should receive the surrounding DOM structure
    Including parent elements, sibling elements, and nearby content

  # --- AI classification tasks ---

  Scenario: AI classifies whether an element functions as a heading
    When the AI processes a heading-like candidate
    Then it should classify whether the element is "functioning as a heading"
    And the classification should be a confidence score, not a binary pass/fail

  Scenario: AI classifies whether a group functions as a card
    When the AI processes a card-like candidate
    Then it should classify whether the group is "functioning as a card"
    And the classification should be a confidence score, not a binary pass/fail

  # --- AI explanation requirements ---

  Scenario: AI provides a plain language explanation
    When the AI classifies a candidate
    Then it should provide a human-readable explanation of why it was classified that way
    And the explanation should be understandable without technical expertise

  Scenario: AI suggests what might be wrong
    When the AI classifies a candidate
    Then it should suggest what accessibility issue might exist
    And the suggestion should be framed as "might" not as a definitive failure
    And the suggestion should never auto-fail WCAG

  # --- Design principle compliance ---

  Scenario: AI never auto-fails WCAG
    When the AI produces classifications and explanations
    Then no output should state that an element "fails" WCAG
    And language should use terms like "appears to", "may", "suggests"

  Scenario: AI explains rather than judges
    When the AI produces explanations
    Then the tone should be descriptive not prescriptive
    And an example of acceptable language is "This appears to function as a heading but is not marked up as one"
    And an example of unacceptable language is "This element fails WCAG 1.3.1"

  Scenario: Deterministic analysis runs before AI
    When the tool processes a page
    Then the DOM rules-based analysis should complete first
    And the visual analysis should complete second
    Then the AI reasoning layer should process only the candidates found by the prior layers
    And the AI should not discover new elements from scratch
