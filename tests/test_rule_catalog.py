"""Behavioral coverage for editable per-ruleset YAML catalogs."""

import unittest

from style_audit.deterministic import analyze_deterministic
from style_audit.models import AuditError
from style_audit.rule_catalog import load_rule_catalog, parse_rule_catalog
from style_audit.text import TextDocument


_REGEX_CATALOG = """schema_version: 1
rules:
  - code: TEST900
    name: Precise wording
    engine: deterministic
    scope: sentence
    source: https://example.invalid/precise-wording
    description: Flag an imprecise adverb.
    detector:
      kind: regex
      pattern: '(?<!\\w)very(?!\\w)'
      flags:
        - ignorecase
      target: unit
      message: Avoid {evidence!r}.
      fix: Replace it with a precise description.
    examples:
      - before: The part is very large.
        after: The part is large.
        explanation: Prefer a measurable description.
"""

_LLM_CATALOG = """schema_version: 1
rules:
  - code: TEST901
    name: Contextual clarity
    engine: llm
    scope: section
    source: https://example.invalid/contextual-clarity
    prompt: Review whether the section preserves the stated distinction.
    examples:
      - before: It may vary.
        after: The setting changes by installation.
        explanation: Name the condition when the source establishes it.
"""


class RuleCatalogTests(unittest.TestCase):
    def test_packaged_rulesets_load_in_stable_order(self):
        codes = [rule.code for rule in load_rule_catalog()]

        self.assertEqual(
            [code[:3] for code in codes],
            ["NAS"] * 24 + ["RDL"] * 7 + ["STE"] * 61,
        )

    def test_yaml_regex_rule_runs_with_unicode_source_positions(self):
        rule, = parse_rule_catalog(_REGEX_CATALOG)
        document = TextDocument(path="draft.md", text="Élan: VERY clear. A verywide path.")

        findings = analyze_deterministic(document, (rule,))

        self.assertEqual(
            [(item.code, item.line, item.column, item.evidence) for item in findings],
            [("TEST900", 1, 7, "VERY")],
        )


    def test_llm_prompt_and_scope_load_from_yaml(self):
        rule, = parse_rule_catalog(_LLM_CATALOG)

        self.assertEqual(rule.engine, "llm")
        self.assertEqual(rule.scope, "section")
        self.assertEqual(
            rule.description,
            "Review whether the section preserves the stated distinction.",
        )

    def test_duplicate_yaml_keys_and_rule_ids_are_rejected(self):
        duplicate_key = _REGEX_CATALOG.replace(
            "schema_version: 1", "schema_version: 1\nschema_version: 1"
        )
        record = _REGEX_CATALOG.split("rules:\n", 1)[1].rstrip()
        duplicate_id = _REGEX_CATALOG.rstrip() + "\n" + record + "\n"

        with self.assertRaisesRegex(AuditError, "duplicate key"):
            parse_rule_catalog(duplicate_key)

        with self.assertRaisesRegex(AuditError, "rule IDs must be unique"):
            parse_rule_catalog(duplicate_id)

    def test_invalid_regex_and_scope_are_rejected(self):
        invalid_regex = _REGEX_CATALOG.replace(r"pattern: '(?<!\w)very(?!\w)'", "pattern: '['")
        invalid_scope = _REGEX_CATALOG.replace("scope: sentence", "scope: sentence_group")

        with self.assertRaises(AuditError):
            parse_rule_catalog(invalid_regex)

        with self.assertRaises(AuditError):
            parse_rule_catalog(invalid_scope)


if __name__ == "__main__":
    unittest.main()
