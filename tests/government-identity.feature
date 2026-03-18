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
    # Step 1 — Locate Contact Information
    When I scan the home page for contact information or a link to a contact page
    Then I should check if the home page directly displays contact information
    Or the home page contains a clearly visible link to a contact page (e.g. "Contact us", "Whakapā mai", or equivalent wording)
    And if neither is present, flag as "Government identity" with reason "FAIL — no contact information or contact page link found on home page"

    # Step 2 — Verify Contact Information Completeness
    When contact information is found or a contact page is linked
    Then I should navigate to the contact information and check for the presence of each requirement:
      | requirement               | description                                                                                      |
      | Email address             | Is one present?                                                                                  |
      | Postal address            | Is one present?                                                                                  |
      | Physical street address   | Is one present?                                                                                  |
      | Phone number              | Is a general telephone number present?                                                           |
      | Call centre number(s)     | Are phone numbers listed for any call centres supporting services on the site?                   |
      | NZ Relay Service link     | Is there a link to the NZ Relay Service (nzrelay.co.nz) for people who are deaf, hard of hearing, deafblind, or have a speech impairment? |
    And each requirement should be marked as PASS, FAIL, or NOT APPLICABLE

    # Step 3 — Output
    Then I should report what was found in Step 1:
      | check                                    | description                                                                 |
      | Contact info on home page                | Was it displayed on the home page? If so, was it marked up with semantic HTML headings? |
      | Contact page link from home page         | If linked, what is the link name and URL?                                   |
      | Footer links (if contact info not found) | If not found on home page, list the names of the links in the footer        |
    And if contact information was found, produce a results table with columns: Requirement | Found | Notes/Evidence
    And give a recommended overall result:
      | result  | criteria                                                        |
      | PASS    | All applicable requirements were found                          |
      | PARTIAL | Some requirements were found — list the gaps                    |
      | FAIL    | No contact information found or not accessible from home page   |

  Scenario: Detect copyright notice
    # Reference: NZ Government Web Usability Standard 1.4, Section 2.4

    # Step 1 — Locate a General Copyright Statement or clearly labelled link
    # NOTE: A bare © symbol or year (e.g. "© 2024 Agency Name") is a copyright NOTICE only.
    # It does NOT constitute a General Copyright Statement and does not satisfy 2.4.1 or 2.4.2.
    When I navigate to the website's home page
    Then I should check if the home page directly displays a substantive General Copyright Statement
    Or the home page contains a visible footer link whose text clearly indicates copyright (e.g. "Copyright", "Manatārua", "Privacy and copyright", or equivalent)
    And if a link is found, I should follow it and read the full copyright statement
    And if only a bare © notice is found with no link, the result is NO COPYRIGHT STATEMENT FOUND

    # Step 2 — Evaluate against mandatory criteria
    When a copyright statement is found
    Then I should evaluate it against each mandatory criterion:
      | criterion | description                                                                                          |
      | 2.4.1     | The website provides access to a General Copyright Statement                                         |
      | 2.4.2     | The statement is on the home page OR linked from the home page with clearly labelled link text       |
      | 2.4.3(a)  | The statement specifies which content on the website it applies to                                   |
      | 2.4.3(b)  | The statement specifies the copyright status of that content                                         |
      | 2.4.3(c)  | The statement specifies the terms under which content can be re-used by others                       |
      | 2.4.4(a)  | If third-party content exists: it is clearly identified (avoiding ambiguity)                         |
      | 2.4.4(b)  | If third-party content exists: its source and copyright status are stated                            |
      | 2.4.4(c)  | If third-party content exists: the statement notes general re-use terms do NOT apply to it           |
      | 2.4.4(d)  | If third-party content exists: the statement notes permission to re-use cannot be given              |
    And I should also note the advisory criteria:
      | criterion | description                                                                                          |
      | 2.4.5     | (advisory) The statement notes that general licensing terms do not apply to material under the Flags, Emblems, and Names Protection Act 1981 |
      | 2.4.6     | (advisory) The NZGOAL framework has been applied when selecting licensing terms                      |

    # Step 3 — Output: exactly one of three outcomes
    Then I should report one of the following outcomes:

    # Outcome A — no copyright found
    And if no copyright statement and no clearly labelled link is found:
      | field       | value                                                                                                |
      | result      | NO COPYRIGHT STATEMENT FOUND                                                                         |
      | checked     | Describe what was looked for and where                                                               |
      | conclusion  | The website does not provide access to a General Copyright Statement as required by 2.4.1 and 2.4.2 |

    # Outcome B — copyright found but fails one or more criteria
    And if a copyright statement exists but fails one or more mandatory criteria:
      | field        | value                                                                                               |
      | result       | COPYRIGHT STATEMENT FOUND — DOES NOT MEET GUIDELINES                                               |
      | where found  | URL or location (e.g. home page footer / link text "Copyright")                                     |
      | how accessed | On home page directly / linked from home page                                                       |
      | failures     | List each failed criterion by number with explanation and quoted evidence                            |
      | passes       | List each criterion that is met with explanation and quoted evidence                                 |

    # Outcome C — copyright meets all mandatory criteria
    And if the copyright statement satisfies all mandatory criteria (2.4.1–2.4.4):
      | field          | value                                                                                             |
      | result         | COPYRIGHT STATEMENT FOUND — MEETS GUIDELINES                                                      |
      | where found    | URL or location                                                                                   |
      | how accessed   | On home page directly / linked from home page                                                     |
      | evidence       | Each criterion listed with ✓ and quoted text from the copyright statement as evidence             |
      | advisory items | Note whether 2.4.5 and 2.4.6 are addressed                                                       |

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
