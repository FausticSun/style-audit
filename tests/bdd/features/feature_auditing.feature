@bdd
Feature: Gherkin feature-file auditing
  Scenario: Only visible prose is audited from feature files
    Given the project configuration:
      """
      [tool.style-audit]
      select = ["NAS001"]
      """
    And a file "draft.feature" containing:
      """
      @robust
      Feature: robust prose boundaries
        @robust
        Scenario: Syntax and fixtures stay hidden
          Given the robust parser reads a feature
            '''
            robust fixture text
            '''
          # robust comment
          | label | value |
          | robust | robust |
      ```
      robust fenced fixture
      ```
      """
    When I run style-audit . --format json
    Then the audit exits with 1
    And the report contains exactly these findings:
      | path          | code   | evidence | line | column | end_column |
      | draft.feature | NAS001 | robust   | 2    | 10     | 16         |
      | draft.feature | NAS001 | robust   | 5    | 15     | 21         |
    And no remote judge was called

