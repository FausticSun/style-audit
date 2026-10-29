"""Behavioral tests for LiteLLM response validation without live credentials."""

from types import SimpleNamespace
import json
import unittest
from unittest.mock import patch

from style_audit.llm import judge_document
from style_audit.models import AuditError
from style_audit.rules import RULES_BY_CODE
from style_audit.text import TextDocument


class LlmJudgmentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.document = TextDocument("draft.md", "The launch marks a pivotal moment for the team.")
        self.rules = (RULES_BY_CODE["NAS106"],)

    def _response(self, content: str):
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])

    def test_valid_finding_is_located_from_controlled_provider_response(self) -> None:
        response = self._response(json.dumps({
            "findings": [{
                "code": "NAS106",
                "evidence": "marks a pivotal moment",
                "reason": "This announces importance without a concrete fact.",
                "fix": "State what changed.",
            }]
        }))
        with patch("style_audit.llm.litellm.completion", return_value=response):
            findings = judge_document(self.document, self.rules, "openai/test-model")
        self.assertEqual(len(findings), 1)
        self.assertEqual((findings[0].line, findings[0].column), (1, 12))
        self.assertEqual(findings[0].evidence, "marks a pivotal moment")
        self.assertEqual(findings[0].code, "NAS106")

    def test_malformed_unknown_and_fabricated_findings_fail_visibly(self) -> None:
        invalid_payloads = (
            "not json",
            '{"findings":[{"code":"NAS999","evidence":"launch","reason":"unsupported"}]}',
            '{"findings":[{"code":"RDL106","evidence":"launch","reason":"disabled ruleset"}]}',
            '{"findings":[{"code":"NAS106","evidence":"fabricated quotation","reason":"unsupported"}]}',
        )
        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                with patch("style_audit.llm.litellm.completion", return_value=self._response(payload)):
                    with self.assertRaises(AuditError):
                        judge_document(self.document, self.rules, "openai/test-model")

    def test_provider_failure_is_not_reported_as_a_clean_document(self) -> None:
        with patch("style_audit.llm.litellm.completion", side_effect=RuntimeError("provider offline")):
            with self.assertRaisesRegex(AuditError, "LiteLLM provider call failed"):
                judge_document(self.document, self.rules, "openai/test-model")

    def test_quoted_examples_cannot_be_cited_as_findings(self) -> None:
        document = TextDocument("draft.md", 'The report says "marks a pivotal moment" as an example.')
        payload = '{"findings":[{"code":"NAS106","evidence":"marks a pivotal moment","reason":"unsupported"}]}'
        with patch("style_audit.llm.litellm.completion", return_value=self._response(payload)):
            with self.assertRaisesRegex(AuditError, "not present in visible prose"):
                judge_document(document, self.rules, "openai/test-model")

    def test_chat_findings_do_not_require_decision_probabilities(self) -> None:
        response = self._response(json.dumps({
            "findings": [{
                "code": "NAS106",
                "evidence": "marks a pivotal moment",
                "reason": "This announces importance without a concrete fact.",
                "fix": "State what changed.",
            }],
        }))
        with patch("style_audit.llm.litellm.completion", return_value=response):
            with patch("style_audit.llm.litellm.systemone") as decision_provider:
                findings = judge_document(
                    self.document, self.rules, "openai/test-model", threshold=1.0
                )
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].evidence, "marks a pivotal moment")
        self.assertEqual(findings[0].fix, "State what changed.")
        decision_provider.assert_not_called()


class DecisionJudgmentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.document = TextDocument("draft.md", "The launch marks a pivotal moment for the team.")
        self.rules = (RULES_BY_CODE["NAS106"],)
        completion = patch(
            "style_audit.llm.litellm.completion",
            side_effect=AssertionError("Decision judging must not use chat completion"),
        )
        self.addCleanup(completion.stop)
        completion.start()

    @staticmethod
    def _response(probabilities):
        return SimpleNamespace(answers={
            code: SimpleNamespace(type="noul", noul=probability)
            for code, probability in probabilities.items()
        })

    def test_probability_at_threshold_emits_a_source_located_finding(self) -> None:
        response = self._response({"NAS106": 0.8})
        with patch("style_audit.llm.litellm.systemone", return_value=response):
            findings = judge_document(
                self.document,
                self.rules,
                "azure-maas-judge/Decision-1",
                threshold=0.8,
            )
        self.assertEqual(len(findings), 1)
        finding = findings[0]
        self.assertEqual(finding.path, "draft.md")
        self.assertEqual(finding.code, "NAS106")
        self.assertEqual(finding.evidence, self.document.text)
        self.assertEqual(
            (finding.line, finding.column, finding.end_line, finding.end_column),
            (1, 1, 1, len(self.document.text) + 1),
        )
        self.assertIn("0.8", finding.message)
        self.assertEqual(finding.fix, "")


    def test_retired_decision_aliases_do_not_fall_back_to_chat(self) -> None:
        for model in (
            "microsoft/microsoft-decision-1",
            "openrouter/microsoft/microsoft-decision-1",
        ):
            with self.subTest(model=model):
                with patch("style_audit.llm.litellm.systemone") as decision_call:
                    with patch("style_audit.llm.litellm.completion") as chat_call:
                        with patch("style_audit.llm.load_decision_api") as load_settings:
                            with self.assertRaisesRegex(AuditError, "retired Decision-1"):
                                judge_document(self.document, self.rules, model)
                decision_call.assert_not_called()
                chat_call.assert_not_called()
                load_settings.assert_not_called()

    def test_probability_below_threshold_is_clean(self) -> None:
        response = self._response({"NAS106": 0.799999})
        with patch("style_audit.llm.litellm.systemone", return_value=response):
            findings = judge_document(
                self.document, self.rules, "azure-maas-judge/Decision-1", threshold=0.8
            )
        self.assertEqual(findings, [])

    def test_each_selected_rule_is_judged_independently(self) -> None:
        rules = (RULES_BY_CODE["NAS109"], RULES_BY_CODE["NAS106"])
        response = self._response({"NAS109": 0.2, "NAS106": 0.9})
        with patch("style_audit.llm.litellm.systemone", return_value=response):
            findings = judge_document(
                self.document, rules, "azure-maas-judge/Decision-1", threshold=0.8
            )
        self.assertEqual([finding.code for finding in findings], ["NAS106"])

    def test_multiple_rules_can_flag_the_same_passage(self) -> None:
        rules = (RULES_BY_CODE["NAS109"], RULES_BY_CODE["NAS106"])
        response = self._response({"NAS109": 0.8, "NAS106": 1})
        with patch("style_audit.llm.litellm.systemone", return_value=response):
            findings = judge_document(
                self.document, rules, "azure-maas-judge/Decision-1", threshold=0.8
            )
        self.assertEqual({finding.code for finding in findings}, {"NAS109", "NAS106"})
        self.assertEqual(len(findings), 2)
        self.assertTrue(all(finding.evidence == self.document.text for finding in findings))

    def test_repeated_unicode_passages_keep_distinct_original_spans(self) -> None:
        document = TextDocument(
            "draft.md", "  🌿 Café changed.\n\nOther prose.\n\n  🌿 Café changed.\n"
        )
        response = self._response({"NAS106": 0.9})
        with patch("style_audit.llm.litellm.systemone", return_value=response):
            findings = judge_document(
                document, self.rules, "azure-maas-judge/Decision-1", threshold=0.8
            )
        self.assertEqual(
            [finding.evidence for finding in findings],
            ["🌿 Café changed.", "Other prose.", "🌿 Café changed."],
        )
        self.assertEqual(
            [(finding.line, finding.column, finding.end_line, finding.end_column)
             for finding in findings],
            [(1, 3, 1, 18), (3, 1, 3, 13), (5, 3, 5, 18)],
        )

    def test_sentences_are_separate_targets_and_outer_whitespace_is_trimmed(self) -> None:
        document = TextDocument(
            "draft.md", " \t🌿 Café.\nSecond sentence. \t\n\nNext paragraph.\n"
        )
        response = self._response({"NAS106": 0.9})
        with patch("style_audit.llm.litellm.systemone", return_value=response):
            findings = judge_document(
                document, self.rules, "azure-maas-judge/Decision-1", threshold=0.8
            )
        self.assertEqual(
            [finding.evidence for finding in findings],
            ["🌿 Café.", "Second sentence.", "Next paragraph."],
        )
        self.assertEqual(
            [(finding.line, finding.column, finding.end_line, finding.end_column)
             for finding in findings],
            [(1, 3, 1, 10), (2, 1, 2, 17), (4, 1, 4, 16)],
        )

    def test_masks_do_not_fragment_a_logical_sentence_into_separate_findings(self) -> None:
        document = TextDocument(
            "draft.md",
            '🌿 Before "a pivotal moment" middle `pivotal()` after.\n\n'
            '```text\nfenced pivotal moment\n```\n\n“a pivotal moment”\n',
        )
        response = self._response({"NAS106": 0.9})
        with patch("style_audit.llm.litellm.systemone", return_value=response):
            findings = judge_document(
                document, self.rules, "azure-maas-judge/Decision-1", threshold=0.8
            )
        self.assertEqual([finding.evidence for finding in findings], [
            '🌿 Before "a pivotal moment" middle `pivotal()` after.',
        ])
        self.assertEqual(
            [(finding.line, finding.column, finding.end_line, finding.end_column)
             for finding in findings],
            [(1, 1, 1, 54)],
        )

    def test_empty_or_fully_masked_documents_need_no_provider(self) -> None:
        for text in (
            "",
            " \t\n\n ",
            '"a pivotal moment"',
            "“a pivotal moment”\n‘another quotation’",
            "`pivotal()`",
            "```text\na pivotal moment\n```\n",
            '"quoted" `code`\n\n```\nfenced\n```\n',
        ):
            with self.subTest(text=text):
                with patch("style_audit.llm.litellm.systemone") as provider:
                    findings = judge_document(
                        TextDocument("draft.md", text), self.rules,
                        "azure-maas-judge/Decision-1", threshold=0.8,
                    )
                self.assertEqual(findings, [])
                provider.assert_not_called()

    def test_answers_must_match_exactly_the_selected_rule_ids(self) -> None:
        rules = (RULES_BY_CODE["NAS109"], RULES_BY_CODE["NAS106"])
        invalid_answers = (
            {},
            {"NAS109": 0.1},
            {"NAS106": 0.1},
            {"NAS109": 0.1, "NAS106": 0.1, "NAS999": 0.1},
            {"NAS109": 0.1, "NAS999": 0.1},
        )
        for probabilities in invalid_answers:
            with self.subTest(probabilities=probabilities):
                response = self._response(probabilities)
                with patch("style_audit.llm.litellm.systemone", return_value=response):
                    with self.assertRaises(AuditError):
                        judge_document(
                            self.document, rules, "azure-maas-judge/Decision-1", threshold=0.8
                        )

    def test_missing_or_non_mapping_answers_are_not_clean_results(self) -> None:
        for response in (
            None,
            SimpleNamespace(),
            SimpleNamespace(answers=None),
            SimpleNamespace(answers=[]),
            SimpleNamespace(answers="NAS106"),
        ):
            with self.subTest(response=response):
                with patch("style_audit.llm.litellm.systemone", return_value=response):
                    with self.assertRaises(AuditError):
                        judge_document(
                            self.document, self.rules, "azure-maas-judge/Decision-1", threshold=0.8
                        )

    def test_wrong_answer_types_and_missing_probabilities_fail_visibly(self) -> None:
        for answer in (
            None,
            SimpleNamespace(),
            SimpleNamespace(type="noul"),
            SimpleNamespace(noul=0.1),
            SimpleNamespace(type="bool", noul=0.1),
            SimpleNamespace(type="noul", noul=None),
        ):
            with self.subTest(answer=answer):
                response = SimpleNamespace(answers={"NAS106": answer})
                with patch("style_audit.llm.litellm.systemone", return_value=response):
                    with self.assertRaises(AuditError):
                        judge_document(
                            self.document, self.rules, "azure-maas-judge/Decision-1", threshold=0.8
                        )

    def test_invalid_probabilities_fail_even_if_they_would_not_reach_threshold(self) -> None:
        for probability in (
            True, False, "0.9", None, [], 0.5j,
            float("nan"), float("inf"), -float("inf"), -0.01, 1.01,
        ):
            with self.subTest(probability=probability):
                response = self._response({"NAS106": probability})
                with patch("style_audit.llm.litellm.systemone", return_value=response):
                    with self.assertRaises(AuditError):
                        judge_document(
                            self.document, self.rules, "azure-maas-judge/Decision-1", threshold=1
                        )

    def test_probability_endpoints_are_valid_and_threshold_is_inclusive(self) -> None:
        for probability, threshold, expected_count in ((0, 0, 1), (0, 1, 0), (1, 1, 1)):
            with self.subTest(probability=probability, threshold=threshold):
                response = self._response({"NAS106": probability})
                with patch("style_audit.llm.litellm.systemone", return_value=response):
                    findings = judge_document(
                        self.document, self.rules, "azure-maas-judge/Decision-1", threshold=threshold
                    )
                self.assertEqual(len(findings), expected_count)

    def test_late_provider_failure_does_not_return_partial_findings(self) -> None:
        document = TextDocument("draft.md", "First visible paragraph.\n\nSecond visible paragraph.")
        with patch("style_audit.llm.litellm.systemone", side_effect=[
            self._response({"NAS106": 0.9}), RuntimeError("decision provider offline"),
        ]):
            with self.assertRaisesRegex(AuditError, "LiteLLM Decisions call failed"):
                judge_document(document, self.rules, "azure-maas-judge/Decision-1", threshold=0.8)

    def test_late_malformed_answer_does_not_return_partial_findings(self) -> None:
        document = TextDocument("draft.md", "First visible paragraph.\n\nSecond visible paragraph.")
        with patch("style_audit.llm.litellm.systemone", side_effect=[
            self._response({"NAS106": 0.9}), self._response({}),
        ]):
            with self.assertRaises(AuditError):
                judge_document(document, self.rules, "azure-maas-judge/Decision-1", threshold=0.8)


    def test_invalid_decision_thresholds_fail_before_provider_calls(self) -> None:
        for threshold in (
            True, False, "0.8", None,
            float("nan"), float("inf"), -float("inf"), -0.01, 1.01,
        ):
            with self.subTest(threshold=threshold):
                with patch("style_audit.llm.litellm.systemone") as provider:
                    with self.assertRaisesRegex(AuditError, "threshold"):
                        judge_document(
                            self.document, self.rules, "azure-maas-judge/Decision-1",
                            threshold=threshold,
                        )
                provider.assert_not_called()


if __name__ == "__main__":
    unittest.main()
