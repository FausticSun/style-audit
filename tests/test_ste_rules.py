"""Behavioral regression coverage for the published ASD-STE100 rule IDs."""

import unittest

from style_audit.rules import RULES


class SimplifiedTechnicalEnglishCatalogTests(unittest.TestCase):
    def test_issue_nine_part_one_has_every_numbered_rule_and_recommendation(self) -> None:
        section_rule_counts = (14, 2, 7, 5, 5, 6, 3, 7, 4)
        expected = {
            f"STE{section}{number:02d}"
            for section, count in enumerate(section_rule_counts, start=1)
            for number in range(1, count + 1)
        } | {f"STEGR{number}" for number in range(1, 9)}
        registered = [rule.code for rule in RULES if rule.code.startswith("STE")]

        self.assertEqual(len(registered), 61)
        self.assertEqual(len(set(registered)), 61)
        self.assertEqual(set(registered), expected)

    def test_only_the_two_measurable_rules_are_local(self) -> None:
        local_codes = {
            rule.code
            for rule in RULES
            if rule.code.startswith("STE") and rule.engine == "deterministic"
        }
        self.assertEqual(local_codes, {"STE606", "STE801"})


if __name__ == "__main__":
    unittest.main()
