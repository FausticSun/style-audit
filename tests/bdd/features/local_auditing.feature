@bdd
Feature: Local prose and Python docstring auditing
  Writers can check visible prose without executing code or contacting a model.

  Background:
    Given the project configuration:
      """
      [tool.style-audit]
      select = ["NAS00"]
      """

  Scenario: A complete word is reported at its original location
    Given a file "draft.md" containing:
      """
      The robustness check passed.
      A robust parser shipped.
      """
    When I run style-audit draft.md --format json
    Then the audit exits with 1
    And the report contains exactly these findings:
      | path     | code   | evidence | line | column | end_column |
      | draft.md | NAS001 | robust   | 2    | 3      | 9          |
    And no remote judge was called

  Scenario: Quoted and fenced examples are not prose violations
    Given a file "examples.md" containing:
      """
      The example uses "robust" as its label.
      `robust`
      ```python
      robust
      ```
      The parser reads an integer.
      """
    When I run style-audit examples.md --format json
    Then the audit exits with 0
    And the reported rule IDs are "none"
    And no remote judge was called

  Scenario: Python reports only a real docstring and does not execute the file
    Given a file "api.py" containing:
      ```
      # A robust comment.
      VALUE = "robust"
      def parse_count():
          """A robust parser."""
          return "robust"
      raise RuntimeError("Audited Python must not execute")
      ```
    When I run style-audit api.py --format json
    Then the audit exits with 1
    And the report contains exactly these findings:
      | path   | code   | evidence | line | column | end_column |
      | api.py | NAS001 | robust   | 4    | 10     | 16         |
    And no remote judge was called

  Scenario Outline: Stdin's filename determines whether comments are prose
    Given standard input:
      """
      # A robust comment.
      VALUE = "robust"
      """
    When I run style-audit - --stdin-filename <filename> --format json
    Then the audit exits with <status>
    And the reported rule IDs are "<rules>"
    And no remote judge was called

    Examples:
      | filename | status | rules  |
      | api.py   | 0      | none   |
      | api.pyi  | 0      | none   |
      | note.txt | 1      | NAS001 |
      | api.feature | 0      | none   |

  Scenario: Invalid Python fails without a partial report
    Given a file "first.md" containing:
      """
      A robust local report.
      """
    And a file "broken.py" containing:
      """
      def broken(:
      """
    When I run style-audit . --format json
    Then there is an operational error and no report
    And the error identifies "broken.py"
    And no remote judge was called

  Scenario: STE local rules distinguish protected punctuation and six-sentence boundary
    Given a file "ste.md" containing:
      """
      The sign reads "Test; Start" and `test; start`.

      Inspect the result; then open the panel.

      The case stores the adapter. It has a lid. The lid has a seal. Two clips secure it. A label shows the model. The hinge allows opening.

      The case has a marker. It shows the size. It names the model. It has a code. It has a seal. It has clips. The base has a seam.
      """
    When I run style-audit ste.md --select STE801,STE606 --format json
    Then the audit exits with 1
    And the report contains exactly these findings:
      | path   | code   | line | column |
      | ste.md | STE801 | 3    | 19     |
      | ste.md | STE606 | 7    | 1      |
    And no remote judge was called

  Scenario: Configured lexical vocabularies apply to NAS and STE rules
    Given the project configuration:
      """
      [tool.style-audit.no-ai-slop]
      allowed-words = ["robust"]
      disallowed-words = ["excellent"]

      [tool.style-audit.ste]
      allowed-words = ["actuator"]
      disallowed-words = ["snapshot"]
      """
    And a file "draft.md" containing:
      """
      The snapshot is disallowed.
      "snapshot" and `snapshot` are quoted examples.
      The robust component works. ROBUSTNESS remains a different term.
      The excellent component serves as a tracker.
      """
    When I run style-audit draft.md --format json
    Then the audit exits with 1
    And the report contains exactly these findings:
      | path     | code   | evidence   | line | column |
      | draft.md | STE101 | snapshot   | 1    | 5      |
      | draft.md | NAS001 | excellent  | 4    | 5      |
      | draft.md | NAS003 | serves as  | 4    | 25     |
    And no remote judge was called
