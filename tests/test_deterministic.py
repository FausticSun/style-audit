"""Behavioral checks for source-backed deterministic rules."""

import unittest

from style_audit.deterministic import analyze_deterministic
from style_audit.rules import RULES_BY_CODE
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
        findings = analyze_deterministic(TextDocument(
            path="draft.md",
            text=source,
        ))
        self.assertEqual([(item.code, item.evidence, item.line, item.column) for item in findings], [
            ("NAS001", "robust", 1, 16),
        ])

    def test_heading_emoji_and_explicit_weak_phrases_are_located(self) -> None:
        source = "# Notes\n## 🧭 Plan\nThe app serves as a tracker; the team made a decision.\nThe system has the ability to score drafts.\n"
        findings = analyze_deterministic(TextDocument(
            path="guide.md",
            text=source,
        ))
        self.assertEqual(
            [(item.code, item.evidence, item.line, item.column) for item in findings],
            [
                ("NAS002", "🧭", 2, 4),
                ("NAS003", "serves as", 3, 9),
                ("STE801", ";", 3, 28),
                ("NAS003", "made a decision", 3, 39),
                ("NAS003", "has the ability to", 4, 12),
            ],
        )

    def test_empty_and_quoted_prose_have_no_findings(self) -> None:
        self.assertEqual(analyze_deterministic(TextDocument(
            path="empty.md",
            text="",
        )), [])
        source = 'The sentence says “delve”, `serves as`, and # 🪴 Example in code:\n'
        self.assertEqual(analyze_deterministic(TextDocument(
            path="quote.md",
            text=source,
        )), [])

    def test_configured_nas_words_override_and_extend_the_banned_list(self) -> None:
        document = TextDocument(
            path="draft.md",
            text="The robust parser works. ROBUSTNESS is a separate term.\nThe excellent parser works.",
        )
        findings = analyze_deterministic(
            document,
            (RULES_BY_CODE["NAS001"],),
            nas_allowed_words=("ROBUST",),
            nas_disallowed_words=("excellent",),
        )
        self.assertEqual(
            [(finding.code, finding.evidence, finding.line, finding.column) for finding in findings],
            [("NAS001", "excellent", 2, 5)],
        )

        denied_overlap = analyze_deterministic(
            TextDocument(
                path="draft.md",
                text="The robust parser works.",
            ),
            (RULES_BY_CODE["NAS001"],),
            nas_allowed_words=("robust",),
            nas_disallowed_words=("ROBUST",),
        )
        self.assertEqual(
            [(finding.evidence, finding.column) for finding in denied_overlap],
            [("robust", 5)],
        )

    def test_paragraph_limit_ignores_markdown_tables(self) -> None:
        table = (
            "| Field | Explanation |\n"
            "| --- | --- |\n"
            "| One | This is one. It is two. |\n"
            "| Two | This is three. It is four. |\n"
            "| Three | This is five. It is six. |\n"
            "| Four | This is seven. It is eight. |\n"
        )
        findings = analyze_deterministic(
            TextDocument(
                path="guide.md",
                text=table,
            ),
            (RULES_BY_CODE["STE606"],),
        )
        self.assertEqual(findings, [])

    def test_configured_ste_disallowed_words_respect_prose_masks(self) -> None:
        document = TextDocument(
            path="technical.md",
            text='“snapshot” and `snapshot` are examples.\nThe snapshot is not approved.\n',
        )
        findings = analyze_deterministic(
            document,
            (RULES_BY_CODE["STE101"],),
            ste_disallowed_words=("SNAPSHOT",),
        )
        self.assertEqual(
            [(finding.code, finding.evidence, finding.line, finding.column) for finding in findings],
            [("STE101", "snapshot", 2, 5)],
        )


if __name__ == "__main__":
    unittest.main()
