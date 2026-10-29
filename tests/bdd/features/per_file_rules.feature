@bdd
Feature: Applying rule patterns to file patterns
  A project can choose different rules for documents while retaining ignore precedence.

  Background:
    Given the project configuration:
      """
      [tool.style-audit]
      select = ["NAS003"]
      ignore = ["NAS002"]
      [tool.style-audit.per-file-select]
      "docs/**" = ["NAS001"]
      "docs/*/draft[12].md" = ["NAS00?"]
      "generated/**" = []
      """

  Scenario: Overlapping entries combine while other files use their own selection
    Given a file "docs/plain.md" containing:
      """
      A robust parser has the ability to read counts.
      """
    And a file "docs/nested/draft1.md" containing:
      """
      A robust parser has the ability to read counts.
      """
    And a file "docs/nested/draft3.md" containing:
      """
      A robust parser has the ability to read counts.
      """
    And a file "fallback.txt" containing:
      """
      A robust parser has the ability to read counts.
      """
    And a file "generated/sample.md" containing:
      """
      A robust parser has the ability to read counts.
      """
    When I run style-audit . --format json
    Then the audit exits with 1
    And the report contains exactly these findings:
      | path                  | code   | evidence           |
      | docs/nested/draft1.md | NAS001 | robust             |
      | docs/nested/draft1.md | NAS003 | has the ability to |
      | docs/nested/draft3.md | NAS001 | robust             |
      | docs/plain.md        | NAS001 | robust             |
      | fallback.txt         | NAS003 | has the ability to |
    And no remote judge was called

  Scenario: Running from a nested directory preserves the configuration root
    Given a file "docs/nested/draft1.md" containing:
      """
      A robust parser has the ability to read counts.
      """
    And I audit from "docs/nested"
    When I run style-audit . --format json
    Then the audit exits with 1
    And the report contains exactly these findings:
      | path                  | code   | evidence           |
      | docs/nested/draft1.md | NAS001 | robust             |
      | docs/nested/draft1.md | NAS003 | has the ability to |

  Scenario: Named stdin inherits file selection
    Given standard input:
      """
      A robust parser has the ability to read counts.
      """
    When I run style-audit - --stdin-filename docs/virtual.md --format json
    Then the audit exits with 1
    And the report contains exactly these findings:
      | path            | code   | evidence |
      | docs/virtual.md | NAS001 | robust   |

  Scenario: CLI glob selection replaces file mappings but cannot undo ignores
    Given a file "docs/plain.md" containing:
      """
      # 🌿 Header
      A robust parser has the ability to read counts.
      """
    When I run style-audit docs/plain.md --select 'NAS00?' --format json
    Then the audit exits with 1
    And the report contains exactly these findings:
      | path          | code   | evidence           |
      | docs/plain.md | NAS001 | robust             |
      | docs/plain.md | NAS003 | has the ability to |
    And no remote judge was called
    When I run style-audit docs/plain.md --select 'NAS00?' --ignore 'NAS00[13]' --format json
    Then the audit exits with 0
    And the reported rule IDs are "none"
    And no remote judge was called

  Scenario: An invalid unused rule selector is not hidden by a CLI override
    Given the project configuration:
      """
      [tool.style-audit.per-file-select]
      "unmatched/**" = ["NAS999"]
      """
    And a file "draft.md" containing:
      """
      A robust parser.
      """
    When I run style-audit draft.md --select NAS001 --format json
    Then there is an operational error and no report
    And the error identifies "NAS999"
    And no remote judge was called
