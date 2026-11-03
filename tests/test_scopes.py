"""Behavioral scope boundaries and context-sensitive judgments without live providers."""

import json
from pathlib import Path
import re
import runpy
from types import SimpleNamespace
import unittest

from unittest.mock import patch

from pydantic import BaseModel, ValidationError

from style_audit.deterministic import analyze_deterministic
from style_audit.llm import judge_document
from style_audit.models import AuditError, Rule
from style_audit.rules import RULES_BY_CODE
from style_audit.text import SourceMap, TextDocument, TextUnit


class TextScopeTests(unittest.TestCase):
    def assert_units(self, document, scope, passages):
        units = document.units(scope)
        self.assertIsInstance(units, tuple)
        self.assertEqual(len(units), len(passages))
        cursor = 0
        for unit, passage in zip(units, passages):
            with self.subTest(scope=scope, passage=passage):
                start = document.text.index(passage, cursor)
                end = start + len(passage)
                self.assertIsInstance(unit, TextUnit)
                self.assertEqual((unit.scope, unit.start, unit.end), (scope, start, end))
                self.assertEqual(document.text[unit.start:unit.end], passage)
                cursor = end
        return units

    def test_pydantic_models_reject_invalid_values_and_freeze_rule_metadata(self) -> None:
        with self.assertRaises(ValidationError):
            TextDocument(
                path="draft.md",
                text=42,
            )
        with self.assertRaises(ValidationError):
            Rule(
                code="NAS999",
                name="Invalid engine",
                engine="unknown",
                description="A test rule.",
                source="test",
                scope="sentence",
                examples=(),
            )

        rule = RULES_BY_CODE["NAS001"]
        with self.assertRaises(ValidationError):
            rule.name = "Changed"


    def test_text_records_are_frozen_base_models(self) -> None:
        source_map = SourceMap(source_text="A.", line_starts=(0,), spans=((0, 1), (1, 2)))
        document = TextDocument(path="draft.md", text="A.", source_map=source_map)
        unit = document.units("sentence")[0]

        self.assertIsInstance(document, BaseModel)
        self.assertIsInstance(source_map, BaseModel)
        self.assertIsInstance(unit, BaseModel)
        for record, field_name, value in (
            (document, "text", "Changed."),
            (source_map, "source_text", "Changed."),
            (unit, "start", 1),
        ):
            with self.subTest(record=type(record).__name__):
                with self.assertRaises(ValidationError):
                    setattr(record, field_name, value)

    def test_abbreviations_initials_and_decimals_do_not_end_sentences(self) -> None:
        cases = (
            (
                "Dr. Élodie paid 3.14 euros. Prof. Rao agreed! Done?",
                ("Dr. Élodie paid 3.14 euros.", "Prof. Rao agreed!", "Done?"),
            ),
            (
                "U.S. firms hired A. B. Chen. They grew.",
                ("U.S. firms hired A. B. Chen.", "They grew."),
            ),
            (
                "Use e.g. apples and pears. Compare i.e. the same inputs.",
                ("Use e.g. apples and pears.", "Compare i.e. the same inputs."),
            ),
        )
        for source, passages in cases:
            with self.subTest(source=source):
                self.assert_units(TextDocument(
                    path="draft.md",
                    text=source,
                ), "sentence", passages)

    def test_terminal_quoted_punctuation_can_end_a_sentence_without_splitting_inner_examples(self) -> None:
        cases = (
            ('She said "Hello." Then left.', ('She said "Hello."', "Then left.")),
            ('She quoted "One. Two." as an example.', ('She quoted "One. Two." as an example.',)),
            ('She said “Hello!” Then left.', ('She said “Hello!”', "Then left.")),
        )
        for source, passages in cases:
            with self.subTest(source=source):
                self.assert_units(TextDocument(
                    path="draft.md",
                    text=source,
                ), "sentence", passages)

    def test_unicode_crlf_soft_wraps_and_unpunctuated_tails_keep_original_offsets(self) -> None:
        source = (
            "  🌿 Café costs 2.50 euros.\r\n"
            "It ships\r\nnext Tuesday!  \r\n\r\n"
            "Tail fragment\r\n"
        )
        document = TextDocument(
            path="draft.md",
            text=source,
        )
        units = self.assert_units(document, "sentence", (
            "🌿 Café costs 2.50 euros.",
            "It ships\r\nnext Tuesday!",
            "Tail fragment",
        ))
        self.assertEqual(
            [document.span(unit.start, unit.end) for unit in units],
            [(1, 3, 1, 27), (2, 1, 3, 14), (5, 1, 5, 14)],
        )

    def test_soft_wrapped_sentences_and_deliberate_fragments_are_not_dropped(self) -> None:
        document = TextDocument(
            path="draft.md",
            text="One\nsoftly wrapped thought. Another thought\nwithout final punctuation\n\nWait. Why?\n\nNo answer",
        )
        self.assert_units(document, "sentence", (
            "One\nsoftly wrapped thought.",
            "Another thought\nwithout final punctuation",
            "Wait.",
            "Why?",
            "No answer",
        ))

    def test_inline_masks_do_not_fragment_sentences_or_logical_paragraphs(self) -> None:
        first = '"An example." Before `v1.2()` middle “quoted ending!” after.\nStill one paragraph.'
        source = " \t" + first + " \t\n\n“wholly masked”\n\nNext visible paragraph.\n"
        document = TextDocument(
            path="draft.md",
            text=source,
        )
        self.assert_units(document, "paragraph", (first, "Next visible paragraph."))
        self.assert_units(document, "sentence", (
            '"An example." Before `v1.2()` middle “quoted ending!” after.',
            "Still one paragraph.",
            "Next visible paragraph.",
        ))

    def test_fences_and_list_item_starts_break_paragraphs_but_soft_wraps_do_not(self) -> None:
        source = (
            "Preamble wrapped\nonto another line.\n\n"
            "Lead before code.\n```md\n# Pretend heading\nignored sentence.\n```\n"
            "After code.\n- First item\n  continuing softly.\n- Second item.\n\nLast paragraph."
        )
        self.assert_units(TextDocument(
            path="draft.md",
            text=source,
        ), "paragraph", (
            "Preamble wrapped\nonto another line.",
            "Lead before code.",
            "After code.",
            "- First item\n  continuing softly.",
            "- Second item.",
            "Last paragraph.",
        ))

    def test_atx_and_setext_headings_are_standalone_paragraph_and_sentence_units(self) -> None:
        document = TextDocument(
            path="draft.md",
            text="Preamble.\r\n# Heading\r\nBody sentence.\r\n\r\nSetext title\r\n====\r\nLast sentence.\r\n",
        )
        passages = ("Preamble.", "# Heading", "Body sentence.", "Setext title\r\n====", "Last sentence.")
        for scope in ("paragraph", "sentence"):
            with self.subTest(scope=scope):
                self.assert_units(document, scope, passages)

    def test_nested_atx_and_setext_sections_are_nonoverlapping_and_ignore_fenced_headings(self) -> None:
        sections = (
            "Preamble.",
            "# Parent\nParent body.",
            "## Child\nChild body.\n```md\n# Not a section\nFake\n====\n```\nAfter code.",
            "Sibling\n-------\nSibling body.",
            "# Final\nFinal body.",
        )
        source = " \t" + "\n\n".join(sections) + "\n"
        document = TextDocument(
            path="draft.md",
            text=source,
        )
        units = self.assert_units(document, "section", sections)
        self.assertTrue(all(left.end <= right.start for left, right in zip(units, units[1:])))
        self.assertEqual(sum("Child body." in source[unit.start:unit.end] for unit in units), 1)
        self.assertEqual(sum("After code." in source[unit.start:unit.end] for unit in units), 1)

    def test_quoted_and_inline_code_headings_do_not_split_sections(self) -> None:
        preamble = 'Preamble.\n"# Quoted heading"\n`## Code heading`\nStill preamble.'
        document = TextDocument(
            path="draft.md",
            text=preamble + "\n\n# Real heading\nActual body.",
        )
        self.assert_units(document, "section", (preamble, "# Real heading\nActual body."))

    def test_headingless_section_and_document_aggregate_all_original_context(self) -> None:
        body = 'First paragraph.\n\n"An example."\n\nSecond paragraph.\n```txt\nmasked\n```\nLast paragraph.'
        document = TextDocument(
            path="draft.md",
            text=" \t" + body + "\r\n ",
        )
        self.assert_units(document, "section", (body,))
        self.assert_units(document, "document", (body,))

    def test_every_scope_skips_empty_or_fully_masked_units(self) -> None:
        for source in ("", " \t\r\n", '"quoted"\n\n`code`', "```md\n# Header\nBody.\n```\n"):
            for scope in ("sentence", "paragraph", "section", "document"):
                with self.subTest(source=source, scope=scope):
                    self.assertEqual(TextDocument(
                        path="draft.md",
                        text=source,
                    ).units(scope), ())


class ScopedJudgmentTests(unittest.TestCase):
    BACKENDS = ("decision", "chat")

    @staticmethod
    def _decision_response(probabilities):
        return SimpleNamespace(answers={
            code: SimpleNamespace(type="noul", noul=probability)
            for code, probability in probabilities.items()
        })

    @staticmethod
    def _chat_response(findings):
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(
            content=json.dumps({"findings": findings})
        ))])

    def judge_with_fixture(self, document, codes, backend, evaluate):
        """A provider identifies fixture semantics, rather than echoing requested inputs."""
        rules = tuple(RULES_BY_CODE[code] for code in codes)
        if backend == "decision":
            def decision_provider(*, state, questions, **kwargs):
                context = "\n".join(value for key, value in state.items() if key != "scope" and isinstance(value, str))
                return self._decision_response({
                    code: 0.95 if evaluate(code, context, state["scope"]) is not None else 0.05
                    for code in questions
                })

            with patch("style_audit.llm.litellm.systemone", side_effect=decision_provider), patch(
                "style_audit.llm.litellm.completion", side_effect=AssertionError("Unexpected chat request")
            ):
                return judge_document(document, rules, "azure-maas-judge/Decision-1")

        def chat_provider(*, messages, **kwargs):
            user_message = next(message for message in messages if message["role"] == "user")
            state = json.loads(user_message["content"])
            context = "\n".join(value for key, value in state.items() if key != "scope" and isinstance(value, str))
            context += "\n" + "\n".join(message["content"] for message in messages if message is not user_message)
            enabled = set(re.findall(r"\bNAS\d{3}\b", "\n".join(
                message["content"] for message in messages if message["role"] == "system"
            )))
            findings = []
            for code in sorted(enabled):
                evidence = evaluate(code, context, state["scope"])
                if evidence is not None:
                    findings.append({"code": code, "evidence": evidence, "reason": "The fixture contains the rule's contextual pattern."})
            return self._chat_response(findings)

        with patch("style_audit.llm.litellm.completion", side_effect=chat_provider), patch(
            "style_audit.llm.litellm.systemone", side_effect=AssertionError("Unexpected decision request")
        ):
            return judge_document(document, rules, "openai/test-model")

    def assert_finding_spans(self, document, findings, expected):
        located = []
        cursor_by_evidence = {}
        for code, evidence in expected:
            start = document.text.index(evidence, cursor_by_evidence.get(evidence, 0))
            end = start + len(evidence)
            cursor_by_evidence[evidence] = end
            located.append((code, evidence, *document.span(start, end)))
        self.assertCountEqual(
            [(item.code, item.evidence, item.line, item.column, item.end_line, item.end_column) for item in findings],
            located,
        )

    def test_mixed_scopes_judge_contextual_patterns_at_their_complete_logical_units(self) -> None:
        contrast = (
            "This is not a speed upgrade.\r\nIt is a safety upgrade.\r\n"
            "The release marks a pivotal moment."
        )
        tools = (
            "# Tools\r\nQueueKit, the scheduler, dispatched the job.\r\n\r\n"
            "QueueKit, the dispatcher, retried the same job."
        )
        source = (
            "  " + contrast + "\r\n\r\n" + tools + "\r\n\r\n"
            "## Results\r\nEach batch took ten seconds.\r\n\r\n"
            "# More results\r\nEach build took ten seconds.\r\n"
        )
        document = TextDocument(
            path="draft.md",
            text=source,
        )

        def evaluate(code, text, scope):
            if code == "NAS101" and "not a speed upgrade" in text and "safety upgrade" in text:
                return "This is not a speed upgrade.\r\nIt is a safety upgrade."
            if code == "NAS106" and "marks a pivotal moment" in text:
                return "marks a pivotal moment"
            if code == "NAS110" and "QueueKit, the scheduler, dispatched the job." in text and "QueueKit, the dispatcher, retried the same job." in text:
                return "QueueKit, the dispatcher, retried the same job."
            if code == "NAS113" and "Each batch took ten seconds." in text and "Each build took ten seconds." in text:
                return "Each build took ten seconds."
            return None

        for backend in self.BACKENDS:
            with self.subTest(backend=backend):
                findings = self.judge_with_fixture(document, ("NAS101", "NAS106", "NAS110", "NAS113"), backend, evaluate)
                expected = (
                    [("NAS101", contrast), ("NAS106", "The release marks a pivotal moment."),
                     ("NAS110", tools), ("NAS113", source.strip())]
                    if backend == "decision" else
                    [("NAS101", "This is not a speed upgrade.\r\nIt is a safety upgrade."),
                     ("NAS106", "marks a pivotal moment"),
                     ("NAS110", "QueueKit, the dispatcher, retried the same job."),
                     ("NAS113", "Each build took ten seconds.")]
                )
                self.assert_finding_spans(document, findings, expected)
                if backend == "decision":
                    for finding in findings:
                        self.assertIn(RULES_BY_CODE[finding.code].scope, finding.message)
                        self.assertEqual(finding.fix, "")

    def test_context_in_other_paragraphs_or_sections_cannot_complete_a_narrower_pattern(self) -> None:
        source = (
            "This is not a speed upgrade.\n\nIt is a safety upgrade.\n\n"
            "# Parent\nQueueKit, the scheduler, dispatched the job.\n\n"
            "## Child\nQueueKit, the dispatcher, retried the same job."
        )
        document = TextDocument(
            path="draft.md",
            text=source,
        )

        def evaluate(code, text, scope):
            if code == "NAS101" and "not a speed upgrade" in text and "safety upgrade" in text:
                return "It is a safety upgrade."
            if code == "NAS110" and "QueueKit, the scheduler, dispatched the job." in text and "QueueKit, the dispatcher, retried the same job." in text:
                return "QueueKit, the dispatcher, retried the same job."
            return None

        for backend in self.BACKENDS:
            with self.subTest(backend=backend):
                self.assertEqual(self.judge_with_fixture(document, ("NAS101", "NAS110"), backend, evaluate), [])

    def test_inline_masks_preserve_paragraph_context_without_becoming_judged_evidence(self) -> None:
        paragraph = 'This is not a speed upgrade.\n`upgrade()`\n“Quoted example.”\nIt is a safety upgrade.'
        document = TextDocument(
            path="draft.md",
            text=" \t" + paragraph + "\n",
        )

        def evaluate(code, text, scope):
            if "not a speed upgrade" in text and "safety upgrade" in text:
                return "It is a safety upgrade."
            return None

        for backend in self.BACKENDS:
            with self.subTest(backend=backend):
                findings = self.judge_with_fixture(document, ("NAS101",), backend, evaluate)
                evidence = paragraph if backend == "decision" else "It is a safety upgrade."
                self.assert_finding_spans(document, findings, [("NAS101", evidence)])
                masked_context = TextDocument(
                    path="draft.md",
                    text='This is not a speed upgrade. "It is a safety upgrade."',
                )
                self.assertEqual(self.judge_with_fixture(masked_context, ("NAS101",), backend, evaluate), [])

    def test_repeated_unicode_evidence_is_anchored_to_each_current_sentence(self) -> None:
        sentence = "🌿 Café marks a pivotal moment."
        source = " \t" + sentence + "\r\n\r\nNo claim here.\r\n\r\n  " + sentence + "\r\n"
        document = TextDocument(
            path="draft.md",
            text=source,
        )

        def evaluate(code, text, scope):
            return "marks a pivotal moment" if "marks a pivotal moment" in text else None

        for backend in self.BACKENDS:
            with self.subTest(backend=backend):
                findings = self.judge_with_fixture(document, ("NAS106",), backend, evaluate)
                evidence = sentence if backend == "decision" else "marks a pivotal moment"
                self.assert_finding_spans(document, findings, [("NAS106", evidence), ("NAS106", evidence)])

    def test_chat_cannot_cite_visible_evidence_from_another_sentence(self) -> None:
        document = TextDocument(
            path="draft.md",
            text="The release marks a pivotal moment.\nThe second sentence only describes its date.",
        )

        def evaluate(code, text, scope):
            if "only describes its date" in text:
                return "marks a pivotal moment"
            return None

        with self.assertRaises(AuditError):
            self.judge_with_fixture(document, ("NAS106",), "chat", evaluate)

    def test_selected_rules_cannot_answer_for_another_scope(self) -> None:
        document = TextDocument(
            path="draft.md",
            text="This is not a speed upgrade. It is a safety upgrade.",
        )
        rules = (RULES_BY_CODE["NAS101"], RULES_BY_CODE["NAS106"])

        def decision_provider(*, state, questions, **kwargs):
            if state["scope"] == "sentence":
                return self._decision_response({"NAS101": 0.95})
            return self._decision_response({code: 0.05 for code in questions})

        def chat_provider(*, messages, **kwargs):
            state = json.loads(next(message["content"] for message in messages if message["role"] == "user"))
            if state["scope"] == "sentence":
                return self._chat_response([{
                    "code": "NAS101", "evidence": "This is not a speed upgrade.",
                    "reason": "A paragraph rule was incorrectly returned for one sentence.",
                }])
            return self._chat_response([])

        for backend, target, provider, model in (
            ("decision", "style_audit.llm.litellm.systemone", decision_provider, "azure-maas-judge/Decision-1"),
            ("chat", "style_audit.llm.litellm.completion", chat_provider, "openai/test-model"),
        ):
            with self.subTest(backend=backend):
                with patch(target, side_effect=provider):
                    with self.assertRaises(AuditError):
                        judge_document(document, rules, model)


class ScopedDeterministicTests(unittest.TestCase):
    def test_selected_rule_keeps_token_locations_and_excludes_other_deterministic_rules(self) -> None:
        source = "  ## 🧭 Plan\r\nÉlodie has the ability to ship a robust parser.\r\n"
        document = TextDocument(
            path="draft.md",
            text=source,
        )
        expected = {
            "NAS001": [("NAS001", "robust", 2, 34)],
            "NAS002": [("NAS002", "🧭", 1, 6)],
            "NAS003": [("NAS003", "has the ability to", 2, 8)],
        }
        for code, locations in expected.items():
            with self.subTest(code=code):
                findings = analyze_deterministic(document, (RULES_BY_CODE[code],))
                self.assertEqual([(item.code, item.evidence, item.line, item.column) for item in findings], locations)
        self.assertEqual(analyze_deterministic(document, ()), [])

    def test_heading_rule_covers_nested_and_setext_headings_once_but_not_fenced_examples(self) -> None:
        source = "  # 🌿 Parent\n  ## 🧭 Child\nBody.\n\n  🪴 Sibling\n---\nOther body.\n```md\n# 🚀 Example\n```\n"
        findings = analyze_deterministic(TextDocument(
            path="draft.md",
            text=source,
        ), (RULES_BY_CODE["NAS002"],))
        self.assertEqual(
            [(item.evidence, item.line, item.column) for item in findings],
            [("🌿", 1, 5), ("🧭", 2, 6), ("🪴", 5, 3)],
        )

    def test_generated_sample_with_nested_fences_never_leaks_into_prose_audit(self) -> None:
        hooks = runpy.run_path(str(Path(__file__).resolve().parents[1] / "docs" / "hooks.py"))
        sample = "# 🚀 Example\n```text\nWe utilize samples.\n```\n````text\nThis serves as a demo.\n````\n~~~~~text\nWe delve into details.\n~~~~~\nA robust example."
        rendered = hooks["_sample"](sample)
        document = TextDocument(
            path="rules.md",
            text=rendered + "\n\nWe utilize the parser.",
        )
        findings = analyze_deterministic(document)
        self.assertEqual(
            [(item.code, item.evidence, item.line, item.column) for item in findings],
            [("NAS001", "utilize", rendered.count("\n") + 3, 4)],
        )


if __name__ == "__main__":
    unittest.main()
