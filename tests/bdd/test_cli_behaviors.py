"""CLI acceptance scenarios bound to Gherkin features."""

import json
import shlex
from types import SimpleNamespace

from pytest_bdd import given, parsers, scenarios, then, when


scenarios("features")


@given("the project configuration:")
def configure_project(project, docstring):
    (project / "pyproject.toml").write_text(docstring + "\n", encoding="utf-8")


@given(parsers.parse('a file "{name}" containing:'))
def write_input(project, name, docstring):
    path = project / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(docstring + "\n", encoding="utf-8")


@given(parsers.parse('I audit from "{directory}"'), target_fixture="audit_directory")
def choose_directory(project, directory):
    path = project / directory
    path.mkdir(parents=True, exist_ok=True)
    return path


@given("standard input:", target_fixture="stdin_text")
def provide_stdin(docstring):
    return docstring + "\n"


@given("a chat judge that fails after finding a violation")
def failing_judge(providers):
    response = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(
        content=json.dumps({"findings": [{
            "code": "NAS106",
            "evidence": "The launch marks a pivotal moment.",
            "reason": "This announces importance without a concrete fact.",
        }]})
    ))])
    providers["chat"].side_effect = [response, RuntimeError("Chat provider unavailable")]


@given("a chat judge returning:")
def chat_judge(providers, docstring):
    providers["chat"].side_effect = None
    providers["chat"].return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=docstring))],
    )


@when(parsers.parse("I run style-audit {arguments}"), target_fixture="audit_result")
def run_audit(invoke_audit, arguments):
    return invoke_audit(shlex.split(arguments))


@then(parsers.parse("the audit exits with {code:d}"))
def check_status(audit_result, code):
    assert audit_result.code == code, audit_result.stderr


@then("the report contains exactly these findings:")
def check_findings(project, audit_result, datatable):
    headers = datatable[0]
    coordinates = {"line", "column", "end_line", "end_column"}
    expected = [
        {key: int(value) if key in coordinates else value for key, value in zip(headers, row, strict=True)}
        for row in datatable[1:]
    ]
    actual = []
    for finding in json.loads(audit_result.stdout)["findings"]:
        item = {key: finding[key] for key in headers}
        if "path" in item and item["path"] != "<stdin>":
            item["path"] = (audit_result.cwd / item["path"]).relative_to(project).as_posix()
        actual.append(item)
    assert actual == expected
    assert audit_result.stderr == ""


@then(parsers.parse('the reported rule IDs are "{rules}"'))
def check_rule_ids(audit_result, rules):
    expected = [] if rules == "none" else rules.split(",")
    assert [finding["code"] for finding in json.loads(audit_result.stdout)["findings"]] == expected
    assert audit_result.stderr == ""


@then("there is an operational error and no report")
def check_operational_error(audit_result):
    assert audit_result.code == 2
    assert audit_result.stdout == ""
    assert audit_result.stderr.strip()


@then(parsers.parse('the error identifies "{identifier}"'))
def check_error_identifier(audit_result, identifier):
    assert identifier in audit_result.stderr


@then("no remote judge was called")
def check_local_only(providers):
    providers["chat"].assert_not_called()


@then(parsers.parse('provider requests exclude "{private_text}"'))
def check_request_privacy(providers, private_text):
    for call in providers["chat"].call_args_list:
        assert private_text not in json.dumps(call.kwargs["messages"])
