Feature: Government Identity Detection
  As an accessibility auditor
  I want to detect government identity elements on a webpage
  So I can verify the presence of required branding, contact, copyright, and privacy elements

  Background:
    Given I navigate to "<url>"

  Scenario: Detect government logo or branding
    When I scan the page for government identity elements
    Then I should check for the presence of an official government logo or crest
    And I should look for NZ Government branding elements (e.g., coat of arms, agency logo)
    And if no government branding is found, flag as "Government identity" for review

  Scenario: Detect contact information
    When I scan the page for contact information
    Then I should look for:
      | element              | description                              |
      | phone number         | a visible phone number or tel: link      |
      | email address        | a visible email or mailto: link          |
      | physical address     | a street or postal address               |
    And if no contact information is found, flag as "Government identity" with reason "No contact information detected"

  Scenario: Detect copyright notice
    When I scan the page footer and body for copyright text
    Then I should look for copyright indicators such as:
      | indicator     |
      | (c) or ©      |
      | "Copyright"   |
      | "Crown copyright" |
    And if no copyright notice is found, flag as "Government identity" with reason "No copyright notice detected"

  Scenario: Detect privacy policy link
    When I scan the page for a privacy policy link
    Then I should look for links with text containing "privacy" (case-insensitive)
    And I should check the footer navigation for a privacy link
    And if no privacy policy link is found, flag as "Government identity" with reason "No privacy policy link detected"

  Scenario: Government identity findings are flagged as patterns not violations
    When government identity elements are detected or missing
    Then each finding should be labelled with type "Government identity"
    And the output should not state that the page fails any WCAG criterion
    And the reason should explain what was or was not found
