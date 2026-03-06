Feature: CAPTCHA Detection
  As an accessibility auditor
  I want to detect CAPTCHA implementations on a webpage
  So I can flag them for accessibility review since CAPTCHAs are a known barrier

  Background:
    Given I navigate to "<url>"

  Scenario: Detect reCAPTCHA or hCaptcha
    When I scan the page for CAPTCHA elements
    Then I should look for:
      | indicator                          | description                          |
      | iframe[src*="recaptcha"]           | Google reCAPTCHA iframe              |
      | iframe[src*="hcaptcha"]            | hCaptcha iframe                      |
      | .g-recaptcha                       | reCAPTCHA container class            |
      | .h-captcha                         | hCaptcha container class             |
      | script[src*="recaptcha"]           | reCAPTCHA script loading             |
      | script[src*="hcaptcha"]            | hCaptcha script loading              |
    And if any are found, flag as "CAPTCHA detected" with the specific CAPTCHA type

  Scenario: Detect image-based or custom CAPTCHA
    When I scan the page for custom CAPTCHA patterns
    Then I should look for:
      | indicator                          | description                          |
      | elements with "captcha" in id/class | custom CAPTCHA containers           |
      | images near form inputs with distorted text | image-based challenges       |
      | "verify you are human" text        | CAPTCHA-related instructions         |
    And if found, flag as "CAPTCHA detected" with reason describing the pattern

  Scenario: CAPTCHA findings explain the accessibility concern
    When a CAPTCHA is detected
    Then the finding should be labelled with type "CAPTCHA detected"
    And the reason should explain that CAPTCHAs can be a barrier for users with disabilities
    And the reason should note that accessible alternatives should be provided
    And the output should not state that the CAPTCHA fails WCAG
