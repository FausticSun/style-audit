@bdd
Feature: Explicit and source-grounded editorial review
  Model findings require an opt-in, valid source evidence, and a successful provider response.

  Scenario: A per-file LLM opt-in never sends local-only files to a provider
    Given the project configuration:
      """
      [tool.style-audit]
      select = ["NAS00"]
      [tool.style-audit.per-file-select]
      "review/*.md" = ["NAS106"]
      [tool.style-audit.llm]
      model = "azure-maas-judge/Decision-1"
      """
    And a file "local.md" containing:
      """
      A robust PRIVATE local report.
      """
    And a file "review/draft.md" containing:
      """
      The launch marks a pivotal moment.
      """
    And a decision judge returning probability 0.95
    When I run style-audit . --format json
    Then the audit exits with 1
    And the report contains exactly these findings:
      | path            | code   | evidence                          | line | column |
      | local.md        | NAS001 | robust                            | 1    | 3      |
      | review/draft.md | NAS106 | The launch marks a pivotal moment. | 1   | 1      |
    And provider requests exclude "PRIVATE"

  Scenario: Explicit LLM selection requires a model before any provider call
    Given the project configuration:
      """
      [tool.style-audit]
      select = ["NAS106"]
      """
    And a file "draft.md" containing:
      """
      The launch marks a pivotal moment.
      """
    When I run style-audit draft.md --format json
    Then there is an operational error and no report
    And no remote judge was called

  Scenario Outline: The decision threshold includes equality
    Given the project configuration:
      """
      [tool.style-audit]
      select = ["NAS106"]
      [tool.style-audit.llm]
      model = "azure-maas-judge/Decision-1"
      threshold = 0.8
      """
    And a file "draft.md" containing:
      """
      The launch marks a pivotal moment.
      """
    And a decision judge returning probability <probability>
    When I run style-audit draft.md --format json
    Then the audit exits with <status>
    And the reported rule IDs are "<rules>"

    Examples:
      | probability | status | rules  |
      | 0.79        | 0      | none   |
      | 0.8         | 1      | NAS106 |

  Scenario: Fabricated chat evidence is an error rather than a clean report
    Given the project configuration:
      """
      [tool.style-audit]
      select = ["NAS106"]
      [tool.style-audit.llm]
      model = "openai/test-model"
      """
    And a file "draft.md" containing:
      """
      The launch marks a pivotal moment.
      """
    And a chat judge returning:
      """
      {"findings":[{"code":"NAS106","evidence":"a quotation absent from the draft","reason":"This claims importance without supporting facts."}]}
      """
    When I run style-audit draft.md --format json
    Then there is an operational error and no report

  Scenario: A later provider failure discards earlier findings
    Given the project configuration:
      """
      [tool.style-audit]
      select = ["NAS106"]
      [tool.style-audit.llm]
      model = "azure-maas-judge/Decision-1"
      """
    And a file "draft.md" containing:
      """
      The launch marks a pivotal moment.
      The next release ships tomorrow.
      """
    And a decision judge that fails after finding a violation
    When I run style-audit draft.md --format json
    Then there is an operational error and no report
    And the error identifies "LiteLLM Decisions call failed"

  Scenario: A selected STE context rule accepts source evidence
    Given a file "draft.md" containing:
      """
      The procedure follows the green lamps to the exit.
      """
    And a chat judge returning:
      """
      {"findings":[{"code":"STE103","evidence":"The procedure follows the green lamps to the exit.","reason":"The verb sense may not express the intended instruction."}]}
      """
    When I run style-audit draft.md --select STE103 --model openai/test-model --format json
    Then the audit exits with 1
    And the report contains exactly these findings:
      | path     | code   | evidence                                           | line | column |
      | draft.md | STE103 | The procedure follows the green lamps to the exit. | 1    | 1      |
