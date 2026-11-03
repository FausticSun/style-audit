"""Canonical NAS, RDL, and ASD-STE100 rule catalogs."""

from .models import Rule, RuleExample, RuleScope
from .ste_rules import STE_RULES

_SOURCE = "https://github.com/petergyang/no-ai-slop/blob/000650b156983f5159695b441477f4e63b25dc85/skills/no-ai-slop/SKILL.md"

_DETERMINISTIC = (
    Rule(
        code="NAS001",
        name="Banned outright words and phrases",
        engine="deterministic",
        description="Flags exact matches for terms the source explicitly lists as banned outright.",
        source=f"{_SOURCE}#words-to-cut",
        scope="sentence",
        examples=(RuleExample(
            before='We utilize the parser.',
            after='We use the parser.',
            explanation='The listed verb can be replaced without changing the action.',
        ),),
    ),
    Rule(
        code="NAS002",
        name="Emoji in headings",
        engine="deterministic",
        description="Flags emoji decorating Markdown headings.",
        source=f"{_SOURCE}#patterns-to-cut",
        scope="section",
        examples=(RuleExample(
            before='# 🚀 Launch',
            after='# Launch',
            explanation='The emoji decorates the heading rather than adding information.',
        ),),
    ),
    Rule(
        code="NAS003",
        name="Weak verb phrases",
        engine="deterministic",
        description="Flags the source's explicit examples 'serves as', 'made a decision', and 'has the ability to'.",
        source=f"{_SOURCE}#editing-principles",
        scope="sentence",
        examples=(RuleExample(
            before='The service has the ability to audit drafts.',
            after='The service can audit drafts.',
            explanation='The direct modal verb preserves the stated capability.',
        ),),
    ),
)

_SUBJECTIVE: tuple[tuple[str, str, str, RuleScope, RuleExample], ...] = (
    (
            "Binary contrasts",
            "Detect formulaic 'not X, but Y' contrasts when stating Y directly would be clearer.",
            "patterns-to-cut",
            "paragraph",
            RuleExample(
                before="The question isn't whether to use retries. It's how many retries to allow.",
                after='How many retries should we allow?',
                explanation='The point is the retry count; the contrast adds no separate constraint. Keep contrasts that convey a relevant correction.',
            ),
        ),
    (
            "Throat-clearing openers",
            "Detect generic opening phrases that delay the point; preserve personal context that earns its place.",
            "patterns-to-cut",
            "paragraph",
            RuleExample(
                before="Here's the thing: the build passed.",
                after='The build passed.',
                explanation='The opener delays the result without supplying personal context.',
            ),
        ),
    (
            "Faux-insight setups",
            "Detect claims that flatter the writer as uniquely insightful without adding substance.",
            "patterns-to-cut",
            "sentence",
            RuleExample(
                before="Here's what nobody tells you: backups need restore tests.",
                after='Backups need restore tests.',
                explanation='The exclusivity claim supplies no evidence and is not needed to state the point.',
            ),
        ),
    (
            "Colon reveals",
            "Detect lowercase dramatic reveals after a colon; allow lists, labels, quotations, titles, code, and grammatical capitalization.",
            "patterns-to-cut",
            "sentence",
            RuleExample(
                before='The best part: it keeps your drafts.',
                after='It keeps your drafts.',
                explanation='The lowercase reveal supplies a dramatic label, not a grammatical need for the colon. Ordinary labels and lists remain valid.',
            ),
        ),
    (
            "Superficial analysis",
            "Detect trailing -ing clauses that claim significance without explaining a concrete mechanism or consequence.",
            "patterns-to-cut",
            "sentence",
            RuleExample(
                before="The release adds file search, highlighting the team's commitment to better workflows.",
                after='The release adds file search.',
                explanation='The trailing clause asserts significance without explaining a mechanism; the revision keeps the stated feature.',
            ),
        ),
    (
            "Importance puffery",
            "Detect inflated claims of importance in place of concrete facts.",
            "patterns-to-cut",
            "sentence",
            RuleExample(
                before='The company launched its first paid plan, marking a pivotal moment.',
                after='The company launched its first paid plan.',
                explanation='The first paid plan is already a concrete fact. Remove the importance claim rather than inventing evidence for it.',
            ),
        ),
    (
            "Interpretive metadiscourse",
            "Detect redundant instructions about what to notice or how to interpret a point.",
            "patterns-to-cut",
            "paragraph",
            RuleExample(
                before='The queue stopped losing jobs. That last part matters more than it sounds.',
                after='The queue stopped losing jobs.',
                explanation='The second sentence tells readers how to react but gives them no additional reason.',
            ),
        ),
    (
            "Weasel attribution",
            "Detect vague appeals to unnamed experts, studies, or reports; do not require attribution for ordinary supported statements.",
            "patterns-to-cut",
            "paragraph",
            RuleExample(
                before='Experts agree that caching reduces latency. In our test, caching cut latency from 8 ms to 2 ms.',
                after='In our test, caching cut latency from 8 ms to 2 ms.',
                explanation='The named test and its measurements are already in the draft; the unnamed experts add no verifiable support.',
            ),
        ),
    (
            "Fake-strong verbs",
            "Detect inflated verb phrases where a direct verb or plain 'is'/'has' is clearer.",
            "patterns-to-cut",
            "sentence",
            RuleExample(
                before='The service serves as a tracker for invoices.',
                after='The service tracks invoices.',
                explanation='The direct verb states the same function without the inflated construction.',
            ),
        ),
    (
            "Synonym cycling",
            "Detect repeated renaming of the same subject solely to avoid repeating a clear term.",
            "patterns-to-cut",
            "section",
            RuleExample(
                before='The agent reviews the draft. The assistant scores the piece. The tool suggests fixes.',
                after='The agent reviews the draft, scores it, and suggests fixes.',
                explanation='Here all three subject labels refer to the same agent, and both object labels refer to the same draft. Keep the identities consistent.',
            ),
        ),
    (
            "Negative listing",
            "Detect stacked 'not X, not Y, but Z' fragments that can state Z directly.",
            "patterns-to-cut",
            "paragraph",
            RuleExample(
                before='Not a dashboard. Not a spreadsheet. A queue.',
                after='A queue.',
                explanation='For a component label, the negative list adds drama rather than a relevant distinction. Keep exclusions that readers actually need.',
            ),
        ),
    (
            "Dramatic fragmentation",
            "Detect stacked dramatic fragments or empty repeated endings; preserve intentional voice and useful cadence.",
            "patterns-to-cut",
            "paragraph",
            RuleExample(
                before='The migration finished. Quietly. Completely. No loose ends.',
                after='The migration finished quietly and completely.',
                explanation='Combine the stacked emphasis while preserving the manner and completion claim. A deliberate single fragment is not automatically wrong.',
            ),
        ),
    (
            "Robotic rhythm",
            "Detect conspicuously repeated sentence or paragraph shapes and uniform punchy cadence.",
            "patterns-to-cut",
            "document",
            RuleExample(
                before='We opened the file.\n\nWe read the code.\n\nWe found the bug.\n\nWe fixed the bug.\n\nWe ran the suite.\n\nWe shipped the patch.',
                after='After opening the file and reading the code, we found and fixed the bug.\n\nWe ran the suite and shipped the patch.',
                explanation='In narrative prose, six identically shaped micro-paragraphs obscure the sequence. Group related actions without claiming that the suite passed; a parallel checklist could be appropriate instead.',
            ),
        ),
    (
            "Rhetorical setups",
            "Detect empty rhetorical teasers or self-answered question-and-answer pairs.",
            "patterns-to-cut",
            "paragraph",
            RuleExample(
                before='What if I told you the test caught a race? Plot twist: it did.',
                after='The test caught a race.',
                explanation='The self-answered teaser withholds a result that can be stated directly.',
            ),
        ),
    (
            "Fake-profound kickers",
            "Detect a final aphorism or cute metaphor that restates or dilutes the preceding concrete point.",
            "patterns-to-cut",
            "document",
            RuleExample(
                before='The queue processed all 12 jobs. In the end, every storm is just a doorway.',
                after='The queue processed all 12 jobs.',
                explanation='The final metaphor supplies no clear takeaway about the observed result.',
            ),
        ),
    (
            "Summary-recap endings",
            "Detect a conclusion that merely repeats the preceding text instead of adding a takeaway or next action.",
            "patterns-to-cut",
            "document",
            RuleExample(
                before='The parser now handles empty files. It also preserves line numbers.\n\nIn conclusion, the parser handles empty files and preserves line numbers.',
                after='The parser now handles empty files and preserves line numbers.',
                explanation='The ending repeats both facts without adding a takeaway or next action.',
            ),
        ),
    (
            "Formatting slop",
            "Detect decorative formatting that impairs the content: mid-sentence bold emphasis, bullets better expressed as prose, and headers for tiny sections. Ignore code and examples.",
            "patterns-to-cut",
            "section",
            RuleExample(
                before='## Result\n\n- The test **passed**.\n- The build **passed**.',
                after='The test and build passed.',
                explanation='For this two-item status note, a heading, bullets, and bold emphasis add structure the content does not need. Longer status lists may warrant that structure.',
            ),
        ),
    (
            "Em dash overuse",
            "Detect decorative or clustered em dashes used as a rhythm crutch; short copy should normally avoid them and long copy should use at most a few when useful.",
            "patterns-to-cut",
            "document",
            RuleExample(
                before='The test passed — finally — and the build completed — without errors.',
                after='The test finally passed, and the build completed without errors.',
                explanation='Three decorative dashes crowd a short sentence; the revision retains both results and the emphasis on finally.',
            ),
        ),
    (
            "Abstraction and concreteness",
            "Flag generic, portable claims or inflated abstractions when the draft provides no concrete fact, mechanism, consequence, name, number, date, or example to support them. Do not invent missing facts.",
            "editing-principles",
            "section",
            RuleExample(
                before='The update transforms the experience. We do not yet have measurements of its effect on review time.',
                after="We do not yet have measurements of the update's effect on review time.",
                explanation='The draft supplies no support for the benefit claim and acknowledges uncertainty. Keep that uncertainty rather than inventing measurements.',
            ),
        ),
    (
            "Voice-preserving clarity",
            "Flag only genuinely tangled sentences, needless passive constructions with no human actor, or empty qualifiers. Preserve useful uncertainty, spoken rhythm, humor, edge, deliberate fragments, and personal context.",
            "editing-principles",
            "sentence",
            RuleExample(
                before='The report, which the team had revised after the incident that occurred during the release, was shared by the team.',
                after='The team revised the report after the release incident and then shared it.',
                explanation='The team and the event order already appear in the original. Unnest the clauses and make the team explicit without deleting useful uncertainty or voice.',
            ),
        ),
    (
            "Filler phrases",
            "Flag a listed filler phrase only when it delays the point in this specific sentence; retain useful spoken rhythm or emphasis.",
            "words-to-cut",
            "sentence",
            RuleExample(
                before="It's worth noting that the service uses port 8003.",
                after='The service uses port 8003.',
                explanation='Here the filler adds neither emphasis nor context; removing it leaves the fact intact.',
            ),
        ),
)

_READABILITY_SOURCE = "https://arxiv.org/html/2610.29162v1"
_READABILITY = (
    Rule(
        code="RDL101",
        name="Long syntactic dependencies",
        engine="llm",
        description="Flag a syntactic dependency only when intervening clauses or modifiers make it difficult to connect "
        "a subject, verb, object, or modifier to its partner. Identify the separated partners and the processing "
        "burden; suggest bringing them closer or splitting the sentence without losing meaning. "
        "Do not flag a sentence merely for its word count, or invent a numeric dependency-length cutoff.",
        source=f"{_READABILITY_SOURCE}#A2",
        scope="sentence",
        examples=(RuleExample(
            before='The report that the manager whom the consultant the board hired advised approved disappeared.',
            after='The board hired the consultant, who advised the manager. The manager approved the report. The report disappeared.',
            explanation='Nested clauses delay the main verb and make it hard to track the report, board, consultant, and manager. The revision makes each participant and action explicit.',
        ),),
    ),
    Rule(
        code="RDL102",
        name="Difficult object relative clauses",
        engine="llm",
        description="Flag an object relative clause, with or without an overt relativizer, only when its noncanonical "
        "word order, embedding, or competing participants makes the roles hard to follow. In an object "
        "relative the modified noun is the relative clause's object, not its subject. Preserve clear, familiar "
        "constructions such as 'the book I read'; do not flag subject relatives or prescribe passive voice universally.",
        source=f"{_READABILITY_SOURCE}#A2.SS1",
        scope="sentence",
        examples=(RuleExample(
            before='The intern the editor the manager praised hired left.',
            after='The manager praised the editor, who hired the intern. The intern left.',
            explanation='The intern is the object of hired, and the editor is the object of praised. Unnest the object relatives so their roles are explicit; clear short object relatives remain valid.',
        ),),
    ),
    Rule(
        code="RDL103",
        name="Ambiguous omitted clause markers",
        engine="llm",
        description="Flag omission of an optional 'that' in an object relative or complement clause, including 'so (that)' "
        "and 'sure (that)', only when it causes a garden path, obscures the clause boundary, or forces rereading "
        "that an explicit marker would avoid. Explain the competing parses without inventing the intended meaning. "
        "Keep clear short omissions; do not lengthen every syntactic alternation or treat optional words as mandatory.",
        source=f"{_READABILITY_SOURCE}#A3.T3",
        scope="sentence",
        examples=(RuleExample(
            before='The coach knew the players assigned to train with the reserve team missed practice.',
            after='The coach knew that the players assigned to train with the reserve team missed practice.',
            explanation='The intended meaning here is knowledge that the players missed practice, not acquaintance with the players. That marks the complement boundary before a long modifier invites the direct-object reading.',
        ),),
    ),
    Rule(
        code="RDL104",
        name="Opaque stacked noun compounds",
        engine="llm",
        description="Flag a compound of three or more nouns in a noun-modifier relationship only when its grouping or "
        "the relations between nouns are unclear. Identify the noun stack and explain the ambiguous relations; "
        "suggest explicit prepositions or a clause without inventing facts. Do not count ordinary adjective "
        "sequences as noun stacks, and preserve familiar, unambiguous terms and necessary domain terminology.",
        source=f"{_READABILITY_SOURCE}#A2.SS1",
        scope="sentence",
        examples=(RuleExample(
            before='The team changed the customer account access exception review policy.',
            after='The team changed the policy for reviewing exceptions to access rules for customer accounts.',
            explanation='Here the policy governs reviews of exceptions to customer-account access rules. Stating those relationships resolves the noun grouping; do not assume this interpretation for a real draft without context.',
        ),),
    ),
    Rule(
        code="RDL105",
        name="Unfamiliar denominal verbs",
        engine="llm",
        description="Flag an ad-hoc verb formed from a noun only when the reader must infer an unclear action or noun-to-verb "
        "conversion obscures the meaning. Identify the converted noun and the interpretation burden; prefer an "
        "explicit action when supported by the sentence. Preserve conventional verbs such as 'bottle', 'email', "
        "and 'park', understandable domain usage, and deliberate wordplay. Do not classify unfamiliar words by rarity alone.",
        source=f"{_READABILITY_SOURCE}#A2.SS1",
        scope="sentence",
        examples=(RuleExample(
            before='Please spreadsheet the complaint.',
            after='Please record the complaint in the spreadsheet.',
            explanation='Here the intended action is recording the complaint, not calculating or analyzing it. State that action; conventional verbs such as email do not need replacement.',
        ),),
    ),
    Rule(
        code="RDL106",
        name="Confusing inanimate-agent mismatches",
        engine="llm",
        description="Flag an inanimate subject with an active verb that normally requires an animate agent only when the "
        "mismatch makes agency or the intended action hard to understand. Identify the subject, verb, and resulting "
        "confusion. Preserve conventional metonymy such as 'the paper argues', clear technical idioms, and intentional "
        "personification or metaphor. Do not ban all inanimate subjects, all active verbs, or invent an unnamed human actor.",
        source=f"{_READABILITY_SOURCE}#A2.SS1",
        scope="sentence",
        examples=(RuleExample(
            before='In the approval procedure, the invoice hopes the reviewer forgives its missing approval.',
            after='In the approval procedure, the reviewer might accept the invoice despite its missing approval.',
            explanation='For literal procedural copy, state whether the reviewer might accept the invoice rather than attributing human feelings to a document. This revision retains the intended uncertainty; deliberate personification could be valid in another context.',
        ),),
    ),
    Rule(
        code="RDL107",
        name="Hard-to-interpret word combinations",
        engine="llm",
        description="Flag an unexpected word pair or short word sequence only when its combination makes the local meaning "
        "hard to predict or reconstruct; explain the interpretation burden and suggest a clearer equivalent only "
        "when the meaning is supported. This is a qualitative readability judgment, not a measurement of corpus "
        "attestation, n-gram probability, surprisal, or perplexity. Do not invent frequency statistics or penalize "
        "proper names, precise technical vocabulary, useful novelty, or clear creative language merely for being uncommon.",
        source=f"{_READABILITY_SOURCE}#A2.SS2",
        scope="sentence",
        examples=(RuleExample(
            before='The instructions omit the deadline, collateralizing instruction latency against deadline intent.',
            after='The instructions omit the deadline.',
            explanation='The financial word combination supplies no reconstructable mechanism. Keep the omission already stated rather than inventing another claim; unusual but clear metaphors remain valid.',
        ),),
    ),
)

RULES: tuple[Rule, ...] = _DETERMINISTIC + tuple(
    Rule(
        code=f"NAS{101 + index:03d}",
        name=name,
        engine="llm",
        description=description,
        source=f"{_SOURCE}#{anchor}",
        scope=scope,
        examples=(example,),
    )
    for index, (name, description, anchor, scope, example) in enumerate(_SUBJECTIVE)
) + _READABILITY + STE_RULES
RULES_BY_CODE = {rule.code: rule for rule in RULES}
