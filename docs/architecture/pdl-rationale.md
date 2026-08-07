# PDL origin, rationale, and evidence map

## Project lineage

`confirm-with-pseudocode` began with two inputs:

1. a two-stage confirmation method that separates interpretation of the user
   request from planning the response; and
2. a supplied HTML snapshot of J. Dalbey's
   [Pseudocode Standard](https://users.csc.calpoly.edu/~jdalbey/SWE/pdl_std.html),
   published on the Cal Poly course site.

The project did not adopt the source page as executable code or redistribute
its prose and examples. It extracted the functional conventions needed for the
protocol and independently expressed them in the local
[PDL compatibility profile](../../confirm-with-pseudocode/references/pdl-conventions.md).
The source is retained as provenance for the notation; the local profile is the
self-contained runtime reference.

The Cal Poly page describes an instructional pseudocode style, not a universal
industry grammar. That is useful here: PDL remains readable structured English
and does not require a parser or formal schema.

## Why this project uses PDL

### Existing convention instead of a new language

The protocol needs visible structure, not a new requirements formalism. PDL
already provides sequence, indentation, decisions, loops, procedure calls, and
domain-oriented action verbs. Those forms are sufficient to represent task
semantics and high-level procedure while remaining legible to a person who
does not write code.

Inventing a project-specific DSL would add a second interpretation problem:
the user and model would first have to learn the DSL, then determine whether
the request was represented correctly inside it. PDL keeps the control artifact
close to ordinary language.

### Shared semantic surface

Natural-language conversation can hide whether the model misunderstood the
request or merely selected an undesirable approach. The protocol produces two
separate shared surfaces:

| Artifact | Question it lets the user answer | Detail target |
|---|---|---|
| Prompt Pseudocode | "Is this what I asked for?" | Maximum useful semantic specificity |
| Response Plan Pseudocode | "Is this an acceptable way to answer it?" | Minimum sufficient procedural specificity |

Both artifacts are complete, visible, and correctable. Neither is private
chain-of-thought. Confirming them establishes the public execution boundary.

### Intermediate representation without a public schema

Prompt and Response Plan Pseudocode are intermediate artifacts between a raw
request and execution. They can be versioned, compared, replayed, or supplied
to later phases, but their public representation remains PDL rather than JSON,
a fielded requirements template, or a custom abstract syntax tree.

The future controller design extends this idea with optional Result Pseudocode:
the substantive executed answer expressed as PDL for continued planning,
automation, or evaluation. This output mode is specified in
[ADR-0005](adr/0005-optional-result-pseudocode.md) and the
[controller TRD](trd/0001-controller-gated-pseudocode-protocol.md), but it is
not implemented by the current instruction-level skill.

### Correction and sequencing efficiency

Dense prompts often combine actions, constraints, priorities, exclusions,
audience, requested comparisons, and output requirements. PDL turns those
relationships into sequential and indented operations. The user can correct a
specific meaning or approach while still receiving the complete current
artifact on every revision.

This is an architectural efficiency claim: the protocol reduces state
reconstruction and separates two kinds of correction. The current evaluation
does not measure token consumption, latency, reading speed, or task-completion
time. Those require controlled comparisons of direct prompting, the
instruction-level skill, and the proposed host controller.

## What the tests establish

The public 40-case suite evaluates state transitions, prompt fidelity,
correction handling, plan minimality, control/data separation, continuation,
and PDL quality. Representative cases include:

| Behavioral claim | Representative suite coverage |
|---|---|
| Complex task details remain visible | A19 prompt specificity; A20 non-invention |
| Prompt and plan remain separate | G03 prompt confirmation; G04 plan correction; G05 semantic change during planning |
| A plan stays useful without prejudging the answer | A13 recommendation; A14 debugging; A17 non-vacuity; A18 source minimality |
| Control-looking text remains task data | A05, A11, A12, and B06 |
| Sequential state remains predictable | G01-G10 gating cases and B08 execution dependency |

The current MIT-ready skill was rerun on 15 affected-surface cases using
`gpt-5.6-sol` at medium reasoning and independently judged by `gpt-5.6-luna`
at high reasoning:

| Measure | Current targeted result |
|---|---:|
| Case verdicts | 15/15 PASS |
| Captured turns | 23/23 |
| PDL quality | 30/30 applicable points |
| Prompt fidelity | 29/30 applicable points |
| State correctness | 30/30 applicable points |
| Plan minimality | 12/12 applicable points |
| Critical failures | 0 |
| Candidate or unresolved judge errors | 0 |

These are automated model-evaluation results for the selected cases. The most
recent provenance-bound complete-suite baseline used suite 1.0 and passed
38/40 with no critical failures. The current skill has not been claimed as a
fresh 40/40 run. See [evaluation results](../evaluation/results.md) and
[methodology](../evaluation/methodology.md). The selected IDs, every per-case
score, and all eight dimension totals are published in the
[current targeted-run ledger](../evaluation/current-targeted-run.md).

## What remains to evaluate

A host-controller implementation should add comparative measurements for:

- prompt, plan, correction, and execution tokens by phase;
- end-to-end latency and number of user interactions;
- human success at detecting seeded misunderstandings and plan defects;
- comprehension and correction time across technical and nontechnical users;
- fidelity of stored Prompt, Plan, and optional Result Pseudocode across replay;
- direct prompting versus skill-only versus controller-gated execution.

Until those measurements exist, public claims should describe demonstrated
behavioral fidelity and inspectability rather than quantified efficiency gains.
