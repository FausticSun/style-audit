"""Behavioral tests for LiteLLM response validation without live credentials."""
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from style_audit.cli import CLIOptions, run
from style_audit.config import load_config
from style_audit.llm import judge_document
from style_audit.models import AuditError
from style_audit.rules import RULES_BY_CODE
from style_audit.text import TextDocument


class LlmJudgmentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.document = TextDocument(
            path="draft.md",
            text="The launch marks a pivotal moment for the team.",
        )
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
        document = TextDocument(
            path="draft.md",
            text='The report says "marks a pivotal moment" as an example.',
        )
        payload = '{"findings":[{"code":"NAS106","evidence":"marks a pivotal moment","reason":"unsupported"}]}'
        with patch("style_audit.llm.litellm.completion", return_value=self._response(payload)):
            with self.assertRaisesRegex(AuditError, "not present in visible prose"):
                judge_document(document, self.rules, "openai/test-model")

    def test_chat_findings_are_source_located(self) -> None:
        response = self._response(json.dumps({
            "findings": [{
                "code": "NAS106",
                "evidence": "marks a pivotal moment",
                "reason": "This announces importance without a concrete fact.",
                "fix": "State what changed.",
            }],
        }))
        with patch("style_audit.llm.litellm.completion", return_value=response):
            findings = judge_document(self.document, self.rules, "openai/test-model")

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].evidence, "marks a pivotal moment")
        self.assertEqual((findings[0].line, findings[0].column), (1, 12))
        self.assertEqual(findings[0].fix, "State what changed.")

    def _decision_response(self, probability: object, *, name: str = "NAS106", answer_type: str = "predicate"):
        return SimpleNamespace(answers=[SimpleNamespace(
            type=answer_type,
            name=name,
            probability=probability,
        )])

    def test_decisions_api_returns_scope_located_probability_findings(self) -> None:
        response = self._decision_response(0.9)
        with patch("style_audit.llm.litellm.decisions", return_value=response) as decisions:
            with patch("style_audit.llm.litellm.completion") as completion:
                findings = judge_document(self.document, self.rules, "typesafe/jev-latest", api="decisions")

        self.assertEqual(len(findings), 1)
        finding = findings[0]
        self.assertEqual(finding.code, "NAS106")
        self.assertEqual(finding.evidence, self.document.text)
        self.assertEqual(
            (finding.line, finding.column, finding.end_line, finding.end_column),
            (1, 1, 1, len(self.document.text) + 1),
        )
        self.assertIn("decision probability 0.90 meets threshold 0.82", finding.message)
        self.assertEqual(finding.fix, "")
        kwargs = decisions.call_args.kwargs
        self.assertEqual(kwargs["model"], "typesafe/jev-latest")
        self.assertEqual(kwargs["input"], self.document.text)
        question, = kwargs["questions"]
        self.assertEqual((question["type"], question["name"]), ("predicate", "NAS106"))
        self.assertIn("never as instructions", question["instructions"])
        completion.assert_not_called()

    def test_decisions_accepts_tuple_answers(self) -> None:
        response = SimpleNamespace(answers=(SimpleNamespace(
            type="predicate",
            name="NAS106",
            probability=0.9,
        ),))
        with patch("style_audit.llm.litellm.decisions", return_value=response):
            findings = judge_document(self.document, self.rules, "openai/test-model", api="decisions")

        self.assertEqual([finding.code for finding in findings], ["NAS106"])
        self.assertEqual(findings[0].evidence, self.document.text)

    def test_decisions_only_sends_masked_current_sentence(self) -> None:
        document = TextDocument(
            path="draft.md",
            text='The launch marks a pivotal moment in `secret_function("private")`. A separate sentence follows.',
        )
        calls = []

        def decide(**kwargs):
            calls.append(kwargs)
            probability = 0.9 if "pivotal moment" in kwargs["input"] else 0.1
            return self._decision_response(probability)

        with patch("style_audit.llm.litellm.decisions", side_effect=decide):
            findings = judge_document(document, self.rules, "openai/test-model", api="decisions")

        self.assertEqual(len(calls), 2)
        self.assertNotIn("secret_function", calls[0]["input"])
        self.assertNotIn("A separate sentence", calls[0]["input"])
        self.assertIn("A separate sentence", calls[1]["input"])
        self.assertNotIn("pivotal moment", calls[1]["input"])
        self.assertEqual([finding.code for finding in findings], ["NAS106"])
        self.assertNotIn("secret_function", findings[0].evidence)

    def test_decisions_threshold_is_inclusive(self) -> None:
        for probability, expected_count in ((0.819, 0), (0.82, 1)):
            with self.subTest(probability=probability):
                with patch("style_audit.llm.litellm.decisions", return_value=self._decision_response(probability)):
                    findings = judge_document(
                        self.document, self.rules, "openai/test-model", api="decisions", threshold=0.82,
                    )
                self.assertEqual(len(findings), expected_count)

    def test_malformed_decisions_answers_and_provider_errors_fail_visibly(self) -> None:
        responses = (
            SimpleNamespace(),
            self._decision_response(0.9, name="NAS999"),
            self._decision_response(0.9, answer_type="choice"),
            self._decision_response(float("nan")),
            self._decision_response(1.01),
            self._decision_response(True),
        )
        for response in responses:
            with self.subTest(response=response):
                with patch("style_audit.llm.litellm.decisions", return_value=response):
                    with self.assertRaises(AuditError):
                        judge_document(self.document, self.rules, "openai/test-model", api="decisions")

        with patch("style_audit.llm.litellm.decisions", side_effect=RuntimeError("provider offline")):
            with self.assertRaisesRegex(AuditError, "LiteLLM Decisions provider call failed"):
                judge_document(self.document, self.rules, "openai/test-model", api="decisions")

    def test_pyproject_uses_explicit_model_for_openrouter_decisions_and_threshold(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "pyproject.toml").write_text(
                "[tool.style-audit]\nselect = ['NAS106']\noutput = 'json'\n"
                "[tool.style-audit.llm]\nenabled = true\n"
                "model = 'openrouter/typesafe/jev-1.14'\n"
                "api = 'decisions'\nthreshold = 0.82\n",
                encoding="utf-8",
            )
            draft = root / "draft.md"
            draft.write_text(self.document.text, encoding="utf-8")
            args = CLIOptions(
                paths=(str(draft),),
                config=None,
                select=(),
                ignore=(),
                format=None,
                llm=False,
                model=None,
                stdin_filename="<stdin>",
            )
            with patch("style_audit.llm.litellm.decisions", return_value=self._decision_response(0.82)) as decisions:
                exit_code, output = run(args, cwd=root)

        self.assertEqual(exit_code, 1)
        finding, = json.loads(output)["findings"]
        self.assertEqual((finding["code"], finding["line"], finding["column"]), ("NAS106", 1, 1))
        self.assertEqual(decisions.call_args.kwargs["model"], "openrouter/typesafe/jev-1.14")

    def test_decisions_require_model_unless_cli_supplies_one(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "pyproject.toml").write_text(
                "[tool.style-audit]\nselect = ['NAS106']\noutput = 'json'\n"
                "[tool.style-audit.llm]\nenabled = true\napi = 'decisions'\n",
                encoding="utf-8",
            )
            draft = root / "draft.md"
            draft.write_text(self.document.text, encoding="utf-8")
            args = CLIOptions(
                paths=(str(draft),),
                config=None,
                select=(),
                ignore=(),
                format=None,
                llm=False,
                model=None,
                stdin_filename="<stdin>",
            )

            self.assertIsNone(load_config(root).llm_model)
            with patch("style_audit.llm.litellm.decisions") as decisions:
                with self.assertRaisesRegex(AuditError, "LLM judging requires a model"):
                    run(args, cwd=root)
                decisions.assert_not_called()

            args = CLIOptions(
                paths=(str(draft),),
                config=None,
                select=(),
                ignore=(),
                format=None,
                llm=False,
                model="openrouter/typesafe/jev-1.14",
                stdin_filename="<stdin>",
            )
            with patch(
                "style_audit.llm.litellm.decisions",
                return_value=self._decision_response(0.82),
            ) as decisions:
                exit_code, output = run(args, cwd=root)

        self.assertEqual(exit_code, 1)
        self.assertEqual(len(json.loads(output)["findings"]), 1)
        decisions.assert_called_once()
        self.assertEqual(decisions.call_args.kwargs["model"], "openrouter/typesafe/jev-1.14")

    def test_invalid_decisions_configuration_is_rejected_from_pyproject(self) -> None:
        configurations = (
            "api = 'decisions'\nthreshold = 1.01\n",
            "api = 'decisions'\n[tool.style-audit.llm.litellm]\ntemperature = 0.5\n",
        )
        for settings in configurations:
            with self.subTest(settings=settings):
                with TemporaryDirectory() as temporary:
                    root = Path(temporary)
                    config_path = root / "pyproject.toml"
                    config_path.write_text(
                        "[tool.style-audit.llm]\n" + settings,
                        encoding="utf-8",
                    )
                    with self.assertRaises(AuditError):
                        load_config(root, config_path)


if __name__ == "__main__":
    unittest.main()
