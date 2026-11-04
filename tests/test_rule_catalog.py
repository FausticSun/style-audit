"""Behavioral coverage for editable per-ruleset YAML catalogs."""

import tempfile
import unittest
from pathlib import Path

from style_audit.deterministic import analyze_deterministic
from style_audit.models import AuditError
from style_audit.rule_catalog import (
    load_project_rule_overrides,
    load_rule_catalog,
    parse_rule_catalog,
    parse_rule_overrides,
)
from style_audit.rules import RULES_BY_CODE
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
            ["NAS"] * 24 + ["RDL"] * 7 + ["STE"] * 61 + ["MWG"] * 13,
        )

    def test_mwg_rules_are_contextual_llm_entries(self):
        rules = tuple(rule for rule in load_rule_catalog() if rule.code.startswith("MWG"))

        self.assertEqual([rule.code for rule in rules], [f"MWG{number:03}" for number in range(1, 14)])
        self.assertTrue(all(rule.engine == "llm" for rule in rules))
        self.assertTrue(all(rule.examples for rule in rules))

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


    def test_project_override_changes_bundled_regex_and_adds_terms_without_mutating_registry(self):
        original = RULES_BY_CODE["NAS001"]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "overrides.yaml").write_text(
                "schema_version: 1\n"
                "overrides:\n"
                "  - code: NAS001\n"
                "    detector:\n"
                "      pattern: '(?<!\\w)robust(?!\\w)'\n"
                "      flags: [ignorecase]\n"
                "    additional-terms: [synergy]\n",
                encoding="utf-8",
            )
            overridden_rules = load_project_rule_overrides(
                root,
                ("overrides.yaml",),
                load_rule_catalog(),
            )

        overridden, = overridden_rules
        self.assertEqual(overridden.code, "NAS001")
        self.assertEqual(overridden.detector.pattern, r"(?<!\w)robust(?!\w)")
        self.assertEqual(overridden.additional_terms, ("synergy",))
        self.assertIs(RULES_BY_CODE["NAS001"], original)
        self.assertNotEqual(original.detector.pattern, overridden.detector.pattern)
        findings = analyze_deterministic(
            TextDocument(
                path="draft.md",
                text="The ROBUST parser works; synergy helps. Robustness differs.",
            ),
            (overridden,),
        )
        self.assertEqual(
            [(item.evidence, item.line, item.column) for item in findings],
            [("ROBUST", 1, 5), ("synergy", 1, 26)],
        )

    def test_rule_override_schema_rejects_unknown_fields_and_duplicate_codes(self) -> None:

        invalid_catalogs = (
            """schema_version: 1
overrides:
  - code: NAS001
    unknown: true
""",
            """schema_version: 1
overrides:
  - code: NAS001
    name: First
  - code: NAS001
    name: Second
""",
        )
        for content in invalid_catalogs:
            with self.subTest(content=content):
                with self.assertRaises(AuditError):
                    parse_rule_overrides(content)


if __name__ == "__main__":
    unittest.main()
