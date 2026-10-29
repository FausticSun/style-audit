"""Source-backed Python docstring auditing without executing input code."""

import inspect
import json
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from style_audit.deterministic import analyze_deterministic
from style_audit.docstrings import extract_docstrings
from style_audit.llm import judge_document
from style_audit.models import AuditError
from style_audit.rules import RULES_BY_CODE


class DocstringTests(unittest.TestCase):
    def setUp(self) -> None:
        for provider in (
            "style_audit.llm.litellm.completion",
            "style_audit.llm.litellm.systemone",
        ):
            guard = patch(
                provider,
                side_effect=AssertionError("Docstring tests must not call live providers"),
            )
            self.addCleanup(guard.stop)
            guard.start()

    @staticmethod
    def _source_span(source: str, spelling: str, start: int = 0):
        offset = source.index(spelling, start)
        end = offset + len(spelling)

        def position(index):
            return source.count("\n", 0, index) + 1, index - source.rfind("\n", 0, index)

        return (*position(offset), *position(end))

    @staticmethod
    def _chat_response(code: str, evidence: str):
        findings = [{"code": code, "evidence": evidence, "reason": "An evidenced style violation."}]
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(
            content=json.dumps({"findings": findings})
        ))])

    @staticmethod
    def _decision_response(probabilities):
        return SimpleNamespace(answers={
            code: SimpleNamespace(type="noul", noul=probability)
            for code, probability in probabilities.items()
        })

    def test_all_definition_kinds_and_nested_docstrings_keep_source_order(self) -> None:
        source = (
            '"""A robust module."""\n'
            '# A robust comment must not become a document.\n'
            'raise RuntimeError("Input must never execute")\n'
            'class Capsule:\n'
            '    """A robust class."""\n'
            '    def method(self):\n'
            '        """A robust method."""\n'
            '        return "robust executable text"\n'
            'async def stream():\n'
            '    """A robust async function."""\n'
            '    pass\n'
            'def outer():\n'
            '    """A robust outer function."""\n'
            '    def inner():\n'
            '        """A robust nested function."""\n'
            '        pass\n'
            '    class Nested:\n'
            '        """A robust nested class."""\n'
        )
        documents = extract_docstrings("definitions.py", source)
        self.assertEqual([document.text for document in documents], [
            "A robust module.", "A robust class.", "A robust method.",
            "A robust async function.", "A robust outer function.",
            "A robust nested function.", "A robust nested class.",
        ])
        findings = [finding for document in documents for finding in analyze_deterministic(document)]
        self.assertEqual(
            [(finding.path, finding.code, finding.evidence, finding.line, finding.column)
             for finding in findings],
            [("definitions.py", "NAS001", "robust", line, column)
             for line, column in ((1, 6), (5, 10), (7, 14), (10, 10),
                                  (13, 10), (15, 14), (18, 14))],
        )

    def test_comments_assigned_and_later_literals_are_not_docstrings(self) -> None:
        source = (
            '# """A robust comment."""\n'
            'ASSIGNED = "A robust assigned string."\n'
            '"A robust later module string."\n'
            'if True:\n'
            '    "A robust conditional string."\n'
            'class NoDoc:\n'
            '    value = "A robust class attribute."\n'
            '    "A robust later class string."\n'
            'def no_doc():\n'
            '    value = "A robust local string."\n'
            '    "A robust later function string."\n'
        )
        self.assertEqual(extract_docstrings("comments.py", source), [])

    def test_non_doc_literals_and_whitespace_docstrings_make_no_findings_or_calls(self) -> None:
        source = (
            'b"A robust bytes literal."\n'
            '"A robust later module string."\n'
            'class BytesFirst:\n'
            '    b"A robust bytes literal."\n'
            '    "A robust later class string."\n'
            'def formatted():\n'
            '    f"A robust {name} string."\n'
            '    "A robust later function string."\n'
            'async def constant_formatted():\n'
            '    f"A robust constant f-string."\n'
            'def empty():\n'
            '    """ \n\t \n    """\n'
        )
        documents = extract_docstrings("literals.py", source)
        self.assertEqual([finding for document in documents for finding in analyze_deterministic(document)], [])
        for model in ("openai/test-model", "azure-maas-judge/Decision-1"):
            with self.subTest(model=model):
                self.assertEqual([
                    finding for document in documents
                    for finding in judge_document(document, (RULES_BY_CODE["NAS106"],), model)
                ], [])

    @unittest.skipUnless(sys.version_info >= (3, 14), "Template strings require Python 3.14")
    def test_template_strings_are_not_docstrings(self) -> None:
        source = (
            't"A robust {name} template."\n'
            'class TemplateFirst:\n'
            '    t"A robust constant template."\n'
            'def template_first():\n'
            '    t"A robust {name} template."\n'
            '    "A robust later string."\n'
        )
        self.assertEqual(extract_docstrings("templates.py", source), [])

    def test_invalid_python_reports_path_and_syntax_location_without_fallback(self) -> None:
        source = '"""A robust preamble."""\ndef broken(:\n    pass\n'
        with self.assertRaises(AuditError) as raised:
            extract_docstrings("broken.py", source)
        message = str(raised.exception)
        self.assertIn("broken.py", message)
        self.assertRegex(message, r"(?:line |:)2(?:[:, ]|$)")
        self.assertRegex(message, r"(?:column |:|, )12\b")

    def test_unicode_and_crlf_findings_use_original_character_columns(self) -> None:
        source = (
            '# Café 🌿\r\n'
            'def café():\r\n'
            '    """Élodie 🌿 wrote a robust parser.\r\n'
            '        The app serves as a tracker.\r\n'
            '    """\r\n'
        )
        documents = extract_docstrings("unicode.py", source)
        self.assertEqual([document.text for document in documents], [
            "Élodie 🌿 wrote a robust parser.\nThe app serves as a tracker."
        ])
        findings = analyze_deterministic(documents[0])
        self.assertEqual(
            [(finding.code, finding.evidence, finding.line, finding.column,
              finding.end_line, finding.end_column) for finding in findings],
            [("NAS001", "robust", 3, 25, 3, 31),
             ("NAS003", "serves as", 4, 17, 4, 26)],
        )
        self.assertEqual(documents[0].evidence(0, len(documents[0].text)),
                         "Élodie 🌿 wrote a robust parser.\r\n        The app serves as a tracker.")

    def test_initial_utf8_bom_is_accepted_and_remains_in_original_columns(self) -> None:
        source = (
            '\ufeff"""Élodie 🌿 wrote a robust parser."""\n'
            '# A robust comment is excluded.\n'
            'VALUE = "robust executable text"\n'
        )
        documents = extract_docstrings("bom.py", source)
        self.assertEqual([document.text for document in documents], ["Élodie 🌿 wrote a robust parser."])
        finding, = analyze_deterministic(documents[0])
        self.assertEqual((finding.evidence, finding.line, finding.column,
                          finding.end_line, finding.end_column), ("robust", 1, 22, 1, 28))
        self.assertEqual(finding.column, source.index("robust") + 1)
        self.assertEqual(documents[0].span(0, len(documents[0].text)),
                         self._source_span(source, documents[0].text))

    def test_unicode_before_a_same_line_docstring_does_not_use_utf8_byte_columns(self) -> None:
        source = 'def café(): """Élodie 🌿 wrote a robust parser."""\r\n'
        document, = extract_docstrings("same_line.py", source)
        self.assertEqual(document.text, "Élodie 🌿 wrote a robust parser.")
        finding, = analyze_deterministic(document)
        self.assertEqual((finding.evidence, finding.line, finding.column,
                          finding.end_line, finding.end_column), ("robust", 1, 33, 1, 39))
        self.assertEqual(document.span(0, len(document.text)),
                         self._source_span(source, document.text))

    def test_escapes_and_adjacent_literals_decode_but_preserve_original_evidence(self) -> None:
        cases = (
            ('"""A \\u0072obust parser."""', r"\u0072obust"),
            ('"""A \\x72o\\142ust parser."""', r"\x72o\142ust"),
            ('"""A \\N{LATIN SMALL LETTER R}obust parser."""',
             r"\N{LATIN SMALL LETTER R}obust"),
            ('("A ro" "bust parser.")', 'ro" "bust'),
            ('("A ro"\n     "bust parser.")', 'ro"\n     "bust'),
            ('"""A ro\\\nbust parser."""', 'ro\\\nbust'),
            ('r"""A robust parser."""', "robust"),
            ("u'A robust parser.'", "robust"),
            ('"A robust parser."', "robust"),
        )
        for literal, spelling in cases:
            with self.subTest(literal=literal):
                source = f"def example():\n    {literal}\n"
                documents = extract_docstrings("escaped.py", source)
                self.assertEqual([document.text for document in documents], ["A robust parser."])
                finding, = analyze_deterministic(documents[0], (RULES_BY_CODE["NAS001"],))
                self.assertEqual(finding.evidence, spelling)
                self.assertEqual(
                    (finding.line, finding.column, finding.end_line, finding.end_column),
                    self._source_span(source, spelling),
                )
                self.assertEqual(documents[0].position(2), self._source_span(source, spelling)[:2])

    def test_raw_docstrings_keep_backslash_sequences_literal(self) -> None:
        value = r"A robust parser with \n notation and \u0072 text."
        source = 'def raw():\n    r"""' + value + '"""\n'
        document, = extract_docstrings("raw.py", source)
        self.assertEqual(document.text, value)
        finding, = analyze_deterministic(document)
        self.assertEqual((finding.evidence, finding.line, finding.column), ("robust", 2, 11))
        self.assertEqual(document.evidence(0, len(document.text)), value)

    def test_chat_and_decision_locate_a_quote_across_adjacent_literals(self) -> None:
        source = 'def adjacent():\n    ("The report marks a pivotal " "moment.")\n'
        document, = extract_docstrings("adjacent.py", source)
        self.assertEqual(document.text, "The report marks a pivotal moment.")
        with patch("style_audit.llm.litellm.completion",
                   return_value=self._chat_response("NAS106", "marks a pivotal moment")):
            finding, = judge_document(document, (RULES_BY_CODE["NAS106"],), "openai/test-model")
        spelling = 'marks a pivotal " "moment'
        self.assertEqual(finding.evidence, spelling)
        self.assertEqual((finding.line, finding.column, finding.end_line, finding.end_column),
                         self._source_span(source, spelling))
        with patch("style_audit.llm.litellm.systemone",
                   return_value=self._decision_response({"NAS106": 0.9})):
            finding, = judge_document(document, (RULES_BY_CODE["NAS106"],),
                                     "azure-maas-judge/Decision-1")
        spelling = 'The report marks a pivotal " "moment.'
        self.assertEqual(finding.evidence, spelling)
        self.assertEqual((finding.line, finding.column, finding.end_line, finding.end_column),
                         self._source_span(source, spelling))

    def test_cleandoc_indentation_and_tabs_preserve_source_positions(self) -> None:
        value = "  First line.\n\t\tA robust parser.\n\t\t\tDetail stays.\n\t\tLast line.\n\t"
        source = 'def clean():\n\t"""' + value + '"""\n'
        document, = extract_docstrings("tabs.py", source)
        self.assertEqual(document.text, inspect.cleandoc(value))
        self.assertEqual(document.text,
                         "First line.\nA robust parser.\n        Detail stays.\nLast line.")
        finding, = analyze_deterministic(document)
        self.assertEqual((finding.evidence, finding.line, finding.column,
                          finding.end_line, finding.end_column), ("robust", 3, 5, 3, 11))
        self.assertEqual(document.position(document.text.index("Detail")), (4, 4))

    def test_equal_docstrings_in_different_functions_keep_distinct_spans(self) -> None:
        source = (
            'def first():\n    """A robust parser."""\n    pass\n'
            'def second():\n    """A robust parser."""\n    pass\n'
        )
        documents = extract_docstrings("repeated.py", source)
        self.assertEqual([document.text for document in documents], ["A robust parser."] * 2)
        for engine in ("deterministic", "chat", "decision"):
            with self.subTest(engine=engine):
                with patch("style_audit.llm.litellm.completion",
                           return_value=self._chat_response("NAS106", "robust")):
                    with patch("style_audit.llm.litellm.systemone",
                               return_value=self._decision_response({"NAS106": 0.9})):
                        findings = [
                            finding for document in documents
                            for finding in (analyze_deterministic(document) if engine == "deterministic"
                                            else judge_document(document, (RULES_BY_CODE["NAS106"],),
                                                "openai/test-model" if engine == "chat"
                                                else "azure-maas-judge/Decision-1"))
                        ]
                expected = [(2, 10, 2, 16), (5, 10, 5, 16)]
                evidence = "robust"
                if engine == "decision":
                    expected = [(2, 8, 2, 24), (5, 8, 5, 24)]
                    evidence = "A robust parser."
                self.assertEqual(
                    [(finding.line, finding.column, finding.end_line, finding.end_column)
                     for finding in findings], expected,
                )
                self.assertEqual([finding.evidence for finding in findings], [evidence] * 2)

    def test_markdown_quoted_and_fenced_examples_remain_exempt_inside_docstrings(self) -> None:
        source = (
            "def examples():\n"
            "    '''A robust parser.\n\n"
            '    The report says "a robust example".\n'
            '    Inline `robust` remains literal.\n\n'
            '    ```python\n'
            '    robust = "robust"\n'
            '    ```\n'
            "    '''\n"
        )
        document, = extract_docstrings("examples.py", source)
        self.assertEqual(
            [(finding.code, finding.evidence, finding.line, finding.column)
             for finding in analyze_deterministic(document)],
            [("NAS001", "robust", 2, 10)],
        )
        for quote in ("a robust example", 'robust = "robust"'):
            with self.subTest(quote=quote):
                with patch("style_audit.llm.litellm.completion",
                           return_value=self._chat_response("NAS106", quote)):
                    with self.assertRaisesRegex(AuditError, "not present in visible prose"):
                        judge_document(document, (RULES_BY_CODE["NAS106"],), "openai/test-model")

    def test_chat_and_decision_quotes_map_decoded_escapes_to_original_spelling(self) -> None:
        source = 'def escaped():\n    """A \\u0072obust\\nparser."""\n'
        document, = extract_docstrings("escaped.py", source)
        self.assertEqual(document.text, "A robust\nparser.")
        with patch("style_audit.llm.litellm.completion",
                   return_value=self._chat_response("NAS106", "robust\nparser")):
            finding, = judge_document(document, (RULES_BY_CODE["NAS106"],), "openai/test-model")
        spelling = r"\u0072obust\nparser"
        self.assertEqual(finding.evidence, spelling)
        self.assertEqual((finding.line, finding.column, finding.end_line, finding.end_column),
                         self._source_span(source, spelling))
        with patch("style_audit.llm.litellm.systemone",
                   return_value=self._decision_response({"NAS101": 0.9})):
            finding, = judge_document(document, (RULES_BY_CODE["NAS101"],),
                                     "azure-maas-judge/Decision-1")
        spelling = r"A \u0072obust\nparser."
        self.assertEqual(finding.evidence, spelling)
        self.assertEqual((finding.line, finding.column, finding.end_line, finding.end_column),
                         self._source_span(source, spelling))

    def test_docstring_document_and_paragraph_scopes_are_independent_and_private(self) -> None:
        source = (
            '# SECRET_COMMENT must not leave the process.\n'
            'def first():\n'
            '    """The first report changed. Details follow.\n\n'
            '    First appendix stays.\n'
            '    """\n'
            '    return "SECRET_FIRST_CODE"\n'
            'def second():\n'
            '    """The second report changed. Details follow.\n\n'
            '    Second appendix stays.\n'
            '    """\n'
            '    return "SECRET_SECOND_CODE"\n'
        )
        documents = extract_docstrings("private.py", source)
        rules = (RULES_BY_CODE["NAS113"], RULES_BY_CODE["NAS101"])
        expected_contexts = [
            {"scope": "document", "text": "The first report changed. Details follow.\n\nFirst appendix stays."},
            {"scope": "paragraph", "text": "The first report changed. Details follow."},
            {"scope": "paragraph", "text": "First appendix stays."},
            {"scope": "document", "text": "The second report changed. Details follow.\n\nSecond appendix stays."},
            {"scope": "paragraph", "text": "The second report changed. Details follow."},
            {"scope": "paragraph", "text": "Second appendix stays."},
        ]
        expected_evidence = [
            "The first report changed. Details follow.\n\n    First appendix stays.",
            "The first report changed. Details follow.",
            "The second report changed. Details follow.\n\n    Second appendix stays.",
            "The second report changed. Details follow.",
        ]
        for engine in ("chat", "decision"):
            with self.subTest(engine=engine):
                contexts = []

                def chat_provider(*, messages, **kwargs):
                    state = json.loads(messages[-1]["content"])
                    index = len(contexts)
                    self.assertEqual(state, expected_contexts[index])
                    contexts.append(state)
                    self.assertNotIn("SECRET_", json.dumps(messages))
                    if index in (0, 1, 3, 4):
                        code = "NAS113" if index in (0, 3) else "NAS101"
                        return self._chat_response(code, expected_contexts[index]["text"])
                    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(
                        content='{"findings":[]}'
                    ))])

                def decision_provider(*, state, questions, **kwargs):
                    index = len(contexts)
                    self.assertEqual(state, expected_contexts[index])
                    contexts.append(state)
                    code = "NAS113" if index in (0, 3) else "NAS101"
                    probability = 0.9 if index in (0, 1, 3, 4) else 0.1
                    return self._decision_response({code: probability})

                with patch("style_audit.llm.litellm.completion", side_effect=chat_provider):
                    with patch("style_audit.llm.litellm.systemone", side_effect=decision_provider):
                        findings = [finding for document in documents for finding in judge_document(
                            document, rules, "openai/test-model" if engine == "chat"
                            else "azure-maas-judge/Decision-1"
                        )]
                self.assertEqual(contexts, expected_contexts)
                self.assertEqual([finding.code for finding in findings], ["NAS113", "NAS101"] * 2)
                self.assertEqual([finding.evidence for finding in findings], expected_evidence)
                self.assertEqual(
                    [(finding.line, finding.column, finding.end_line, finding.end_column)
                     for finding in findings],
                    [self._source_span(source, evidence) for evidence in expected_evidence],
                )

    def test_chat_cannot_cite_excluded_executable_code_or_another_function(self) -> None:
        source = (
            '# marks a pivotal moment\n'
            'def first():\n'
            '    """The first report stays concrete."""\n'
            '    return "marks a pivotal moment"\n'
            'def second():\n'
            '    """The second report marks a pivotal moment."""\n'
        )
        first, second = extract_docstrings("private.py", source)
        response = self._chat_response("NAS106", "marks a pivotal moment")
        with patch("style_audit.llm.litellm.completion", return_value=response):
            with self.assertRaisesRegex(AuditError, "not present in visible prose"):
                judge_document(first, (RULES_BY_CODE["NAS106"],), "openai/test-model")
            finding, = judge_document(second, (RULES_BY_CODE["NAS106"],), "openai/test-model")
        self.assertEqual((finding.evidence, finding.line, finding.column),
                         ("marks a pivotal moment", 6, 26))


if __name__ == "__main__":
    unittest.main()
