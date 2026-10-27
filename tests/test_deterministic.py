"""Behavioral checks for source-backed deterministic rules."""

import unittest

from style_audit.deterministic import analyze_deterministic
from style_audit.text import TextDocument


class DeterministicRuleTests(unittest.TestCase):
    def test_banned_term_boundaries_exempt_quotes_and_code(self) -> None:
        source = (
            "Élodie wrote a robust parser.\n"
            'She quoted "a robust example".\n'
            "Inline `robust` stays literal.\n"
            "```text\nrobust\n```\n"
            "Robustness is a different word."
        )
        findings = analyze_deterministic(TextDocument("draft.md", source))
        self.assertEqual([(item.code, item.evidence, item.line, item.column) for item in findings], [
            ("NAS001", "robust", 1, 16),
        ])

    def test_heading_emoji_and_explicit_weak_phrases_are_located(self) -> None:
        source = "# Notes\n## 🧭 Plan\nThe app serves as a tracker; the team made a decision.\nThe system has the ability to score drafts.\n"
        findings = analyze_deterministic(TextDocument("guide.md", source))
        self.assertEqual(
            [(item.code, item.evidence, item.line, item.column) for item in findings],
            [
                ("NAS002", "🧭", 2, 4),
                ("NAS003", "serves as", 3, 9),
                ("NAS003", "made a decision", 3, 39),
                ("NAS003", "has the ability to", 4, 12),
            ],
        )

    def test_empty_and_quoted_prose_have_no_findings(self) -> None:
        self.assertEqual(analyze_deterministic(TextDocument("empty.md", "")), [])
        source = 'The sentence says “delve”, `serves as`, and # 🪴 Example in code:\n'
        self.assertEqual(analyze_deterministic(TextDocument("quote.md", source)), [])


if __name__ == "__main__":
    unittest.main()
