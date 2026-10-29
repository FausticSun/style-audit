# No AI slop

`NAS` adapts [Peter Yang's no-ai-slop guidance](https://github.com/petergyang/no-ai-slop/blob/000650b156983f5159695b441477f4e63b25dc85/skills/no-ai-slop/SKILL.md), pinned to commit `000650b`, under the [MIT license](https://github.com/petergyang/no-ai-slop/blob/000650b156983f5159695b441477f4e63b25dc85/LICENSE). The repository includes its license notice in `third_party/no-ai-slop-LICENSE`.

The rules combine narrow local patterns with contextual editorial judgments. Preserve personal voice, useful uncertainty, and intentional cadence rather than rewriting every unusual phrase. Each card identifies its engine and canonical audit scope.

<!-- rule-cards -->

## Usage

Run only the deterministic rules, without contacting a provider:

```sh
style-audit draft.md --select NAS00
```

To include the no-ai-slop LLM rules, select the ruleset and provide a model explicitly:

```sh
style-audit draft.md --select NAS --model azure-maas-judge/Decision-1 --threshold 0.8
```

`NAS1` selects only its LLM rules. Combine rulesets with `--select NAS00,RDL` for local no-ai-slop checks plus [readability review](readability.md). See [selection and ignore precedence](../configuration.md#selection-ignoring-and-llm-opt-in), [LLM review and privacy](../llm.md), and the [ruleset overview](rules.md).
