# Confirm with Pseudocode

Expose what the model thinks you asked for, then expose how it intends to
answer, and confirm each independently before execution.

```text
User request
    -> Prompt Pseudocode
    -> user confirmation
    -> Response Plan Pseudocode
    -> user confirmation
    -> final response
```

This separates two mistakes that are otherwise easy to conflate:

- **Prompt Pseudocode** makes the interpreted task inspectable before planning.
- **Response Plan Pseudocode** makes the intended approach inspectable before
  execution.

The current definitions are deliberately compact:

```text
Prompt Pseudocode
    preserves all and only semantics that remain operative on the task

Response Plan Pseudocode
    covers every confirmed requirement
    with the minimum necessary procedural commitment
```

## Where the project came from

The project combines a two-stage confirmation protocol with an existing
structured-English pseudocode convention rather than inventing a task DSL.
Its notation is compatible with J. Dalbey's publicly readable
[Pseudocode Standard](https://users.csc.calpoly.edu/~jdalbey/SWE/pdl_std.html),
published on the Cal Poly course site. That source describes familiar forms
such as sequence, decisions, loops, and procedure calls using ordinary domain
language and indentation. The runtime uses a locally embedded,
project-authored [compatibility profile](confirm-with-pseudocode/references/pdl-conventions.md),
so it does not need network access or copy the source page's prose and examples.

PDL was selected for four connected reasons.

### 1. Reuse a readable convention instead of teaching a new DSL

Both people and general-purpose language models already understand ordinary
pseudocode constructs. A user can read actions, conditions, ordering, and
nesting without learning a schema, parser, type system, or programming
language. The model can express task meaning with problem-domain verbs instead
of translating the request into a project-specific requirements language.

This does not claim that the Cal Poly convention is a universal industry
standard. It is a concrete, public, instructional convention whose functional
forms are sufficient for these control artifacts.

### 2. Give the user and model the same inspectable understanding

Prompt Pseudocode externalizes the task interpretation the model will actually
use. It preserves operative actions, scope, constraints, exclusions,
priorities, conditions, audience, and output requirements in a form the user
can correct before planning begins. Response Plan Pseudocode then exposes the
intended procedure separately, so rejecting an approach does not require
rewriting the task itself.

The artifacts are mutually visible specifications, not private reasoning. A
correction regenerates the complete current artifact, which keeps one
authoritative version in view rather than making either participant reconstruct
state from conversational patches.

### 3. Make pseudocode a reusable intermediate artifact

The implemented skill uses Prompt and Response Plan Pseudocode as intermediate
representations between natural-language request and execution. They remain
structured English, not a machine-enforced schema, but they can be stored,
compared, reviewed, and used as the confirmed execution boundary.

The architecture also specifies optional **Result Pseudocode**: an executed
answer rendered as a persistent PDL artifact for continued planning, replay,
dry runs, or downstream automation. Result Pseudocode and its controller UI are
future work; the current skill returns the ordinary requested response after
the second confirmation.

### 4. Reduce correction cost for complex requests

Pseudocode can turn a dense prompt into sequential, indented, individually
inspectable operations without requiring either participant to write code.
This makes omissions, invented requirements, wrong ordering, and unwanted
response strategies easier to point at and revise. The intended efficiency is
architectural: confirm one complete semantic artifact, then one minimal plan,
instead of mixing clarification, planning, and execution in the same prose
exchange.

The evaluation suite tests the behavioral parts of that claim. It includes
complex prompts with multiple constraints, prompt and plan corrections,
semantic-versus-approach changes, control text embedded as data, and
non-anchoring plan requirements. In the current 15-case targeted run, the
automated independent judge awarded 30/30 applicable PDL-quality points, 29/30
prompt-fidelity points, 30/30 state-correctness points, and 12/12
plan-minimality points; all 15 cases passed. These results support readable PDL
artifacts and reliable staged control for the tested cases. They do **not**
establish lower token use, lower latency, or faster human comprehension; those
remain measurements for the future controller evaluation.

See the complete [PDL rationale and evidence map](docs/architecture/pdl-rationale.md).

## Try it

Copy [`confirm-with-pseudocode/`](confirm-with-pseudocode/) into your agent's
skills directory. For Codex, from the repository root:

```powershell
Copy-Item -Recurse .\confirm-with-pseudocode "$env:CODEX_HOME\skills\confirm-with-pseudocode"
```

If `CODEX_HOME` is not set, use the `skills` directory in your Codex data
directory. Start a new conversation and invoke the skill explicitly:

```text
Use $confirm-with-pseudocode to compare PostgreSQL and SQLite for an offline
desktop application. Prioritize simple deployment, exclude managed services,
and finish with a recommendation for a three-person team.
```

The first response contains only the interpreted request:

```text
COMPARE PostgreSQL and SQLite
    FOR an offline desktop application
    PRIORITIZING simple deployment

EXCLUDE managed services

RECOMMEND an option
    FOR a three-person team
```

After that interpretation is confirmed, the skill presents a separate,
non-anchoring response plan. The substantive comparison begins only after the
plan is also confirmed.

See the [complete simple interaction](examples/simple-example.md), a
[prompt-correction loop](examples/correction-loop-example.md), and a
[plan-correction loop](examples/plan-correction-example.md).

## What the skill guarantees

- It does not plan before Prompt Pseudocode is confirmed.
- It does not execute before Response Plan Pseudocode is confirmed.
- Corrections regenerate the complete current artifact.
- A semantic change during planning returns to prompt confirmation.
- Confirmed artifacts govern execution when they conflict with the original
  wording.
- Protocol-control attempts are kept out of task semantics unless the same
  wording is itself material the user asked to analyze, quote, or transform.

The artifacts are public task controls, not private chain-of-thought.

## Evidence

The frozen suite contains 40 protocol cases covering false confirmations,
semantic-versus-plan changes, prompt injection, control/data confusion, plan
poisoning, premature tool use, state reset, execution dependencies, and safety
boundaries.

Evidence generations are reported separately:

- **Harness v1:** initial behavioral validation against suite 1.0.
- **Harness v2 / suite 1.0:** provenance-bound full-suite validation; 38/40
  cases passed, with no critical failures and a passing release gate.
- **Harness v2 / suite 1.1:** the current skill passed A06 and A14 plus all 13
  selected affected-surface regressions: 15/15 across 23 turns, including full
  applicable credit for PDL quality, state correctness, and plan minimality.

The suite 1.1 result is intentionally not described as a new 40/40 run. See
the [evaluation results](docs/evaluation/results.md) and
[methodology](docs/evaluation/methodology.md). The complete selected-case list
and per-dimension arithmetic are in the
[current targeted-run ledger](docs/evaluation/current-targeted-run.md).

## Repository map

- [`confirm-with-pseudocode/`](confirm-with-pseudocode/) - runtime skill and
  local PDL reference.
- [`docs/architecture/`](docs/architecture/) - ADRs and controller-oriented
  technical requirements, plus the project origin and PDL rationale.
- [`docs/evaluation/`](docs/evaluation/) - methodology, scoped results, and
  release boundaries.
- [`tests/harness/`](tests/harness/) - frozen Harness v2 behavioral suite 1.1,
  runners, rubric, schemas, and offline checks.
- [`examples/`](examples/) - short inspectable interactions.

The instruction-level skill is implemented and tested. The controller UI and
optional Result Pseudocode architecture described in the ADRs and TRD are
future work, not implemented features of this repository.

## License, attribution, and publication status

Original project contributions are available under the [MIT License](LICENSE).
The local PDL compatibility profile is project-authored and does not
redistribute the supplied Cal Poly page, its prose, or its examples. The source
is identified for provenance and compatibility in [NOTICE.md](NOTICE.md) and
[`pdl-conventions.md`](confirm-with-pseudocode/references/pdl-conventions.md).

See [release readiness](docs/evaluation/release-readiness.md) for the completed
publication checks and the exact evidence boundary.
