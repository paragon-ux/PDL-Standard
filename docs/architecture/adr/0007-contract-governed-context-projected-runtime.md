# ADR-0007: Adopt a contract-governed, context-projected runtime

- Status: Accepted
- Date: 2026-08-07
- Parent decision: [ADR-0001: Controller-gated pseudocode protocol](0001-controller-gated-pseudocode-protocol.md)
- Preserves:
  - [ADR-0002: Controller-owned artifact controls](0002-controller-owned-artifact-controls.md)
  - [ADR-0004: Confirmed artifacts as execution boundary](0004-confirmed-artifacts-as-execution-boundary.md)
  - [ADR-0006: Bounded pre-execution reasoning](0006-bounded-pre-execution-reasoning.md)
- Refines implementation priority from:
  - [ADR-0003: Phase-projected single-model contexts](0003-phase-projected-single-model-contexts.md)
- Related requirements:
  - [TRD-0001: Controller-gated pseudocode protocol](../trd/0001-controller-gated-pseudocode-protocol.md)
  - [TRD-0002: Contract substrate and mechanical runtime verification](../trd/0002-contract-substrate-and-mechanical-verification.md)

## Context

The instruction-level skill has demonstrated that separate Prompt Pseudocode and
Response Plan Pseudocode can expose task interpretation and response approach
before execution. The remaining architecture problem is no longer only state
control. It is also **context authority**: what instructions, artifacts, source
material, examples, evaluation material, and repository documents are allowed
to influence each phase.

Manual cross-model trials exposed three distinct failure classes:

1. a partial installation omitted a required local reference;
2. execution introduced a new ranking hierarchy after a different hierarchy had
   been confirmed; and
3. execution broadened an operative definition without exposing that definition
   before confirmation.

The first class is mechanically decidable. The latter two require semantic
judgment. A deterministic controller can enforce state and artifact identity but
cannot prove free-form semantic conformance. Conversely, a probabilistic judge
can identify possible semantic drift but must not become a hidden source of
user intent.

The existing repository also contains runtime instructions, architecture
records, evaluation material, examples, harnesses, and release evidence. If an
agent discovers unspecified repository prose during execution and treats it as
operative instruction, repository search becomes an accidental hidden context
compiler.

A stable architecture therefore needs separate answers to four questions:

- **What defines correct protocol behavior?**
- **What context is active in a given phase?**
- **How is conformance checked?**
- **What material may improve model performance without changing correctness?**

## Decision

Adopt a **contract-governed, context-projected runtime with typed verification
and controller-owned state**.

The architecture SHALL have the following authority and governance layers.

### 1. Standard Contracts

Standard Contracts are the sole normative source for model-independent protocol
and runtime requirements.

Every normative requirement SHALL receive a stable requirement ID.

A requirement SHALL NOT be independently paraphrased as normative behavior in
an Execution Contract, Verification Contract, Calibration Contract, controller,
worker prompt, or verifier implementation.

If changing a statement changes what constitutes correct protocol behavior, the
statement belongs in a Standard Contract.

### 2. Confirmed PDL artifacts

Standard Contracts define system behavior. Confirmed PDL artifacts define the
current task.

- Confirmed Prompt Pseudocode is authoritative for **what** the user requested.
- Confirmed Response Plan Pseudocode is authoritative for the approved
  high-level **how**.

Confirmed artifact text SHALL cross system boundaries verbatim with identity,
version, and digest metadata. A summary SHALL NOT replace confirmed artifact
content.

### 3. Execution Contract

A single Execution Contract SHALL define orchestration and context applicability.

It MAY specify:

- which Standard IDs apply in a known phase;
- which worker receives them;
- what source handles accompany them;
- what information crosses a handoff;
- what context is excluded or discarded;
- when verification occurs; and
- which event permits progression.

It SHALL NOT redefine Standard requirements or invent task semantics.

Where applicability depends on qualitative user meaning rather than a known
phase or typed capability, the Execution Contract SHALL NOT silently decide the
meaning from prose.

### 4. Verification Contract

A single inspectable Verification Contract SHALL declare conformance checks and
classify each check by epistemic mechanism:

- `M` — **Mechanical**: deterministically executable from machine-addressable
  inputs;
- `S` — **Semantic**: probabilistic conformance judgment performed in an
  independent projected context; or
- `H` — **Human**: semantic authority resolved by explicit user confirmation or
  review.

Verification code MAY implement Standard requirements. It MUST NOT define new
requirements.

A model-readable checklist is an inspectable verification specification, not a
source of deterministic truth. Mechanical checks SHALL be executed by
reproducible code when a deterministic predicate exists.

### 5. Calibration Contract

Calibration material SHALL contain examples, mutations, dry runs, and
model-specific guidance that improve performance against existing Standards.

Calibration is non-normative and SHALL NOT define correctness. It SHOULD remain
outside routine runtime context unless a known failure mode, evaluation, or
optimization workflow justifies loading it.

If removing a calibration example changes the definition of correctness, the
missing rule belongs in a Standard Contract.

### 6. Runtime manifest

A non-normative machine-readable runtime manifest SHALL identify the currently
installable package and its mechanically verifiable integrity requirements.

The manifest SHALL support deterministic detection of partial installations,
missing required files, undeclared package files, and declared content-identity mismatch.

The manifest is packaging metadata. It SHALL NOT contain semantic rules.

### 7. Context-projected workers

Prompt generation, Plan generation, Execution, and semantic-conformance review
SHALL be modeled as stateless role invocations with positive-inclusion context
projections.

A worker MAY be implemented as a host subagent, separate task/session, or
stateless provider call. Session and context isolation are the architectural
requirements; a provider-specific subagent API is not.

Complete conversation history SHALL NOT be a default phase input.

### 8. Controller-owned state

The future controller/orchestrator SHALL own:

- protocol state and transitions;
- artifact authority and versions;
- source handles;
- context compilation;
- worker routing;
- verification routing;
- bounded retry policy; and
- final delivery policy.

No worker or verifier may independently select the next authoritative protocol
state.

### 9. Source-bound semantics

When a confirmed artifact clause delegates operative meaning to source
material, the system SHALL either expose the delegated meaning in the artifact
or bind the clause to an immutable or versioned source handle and selector.

For example, a confirmed clause such as `IMPLEMENT all requirements in section
4` cannot be preserved by passing those words alone. Workers whose decisions
depend on that clause must receive the same bound section or an equivalent
versioned source handle.

### 10. Semantic-remediation boundary

Semantic conformance findings SHALL distinguish at least:

- **artifact-entailed drift** — a contradiction or omission demonstrable from
  confirmed text; and
- **interpretive drift** — a finding whose resolution requires choosing among
  plausible meanings not settled by the confirmed artifacts.

Artifact-entailed drift MAY trigger one bounded automatic retry.

Interpretive drift MUST NOT cause the evaluator to invent replacement semantics.
It MAY be disclosed or returned to the user when material.

Evaluator confidence alone does not create semantic authority.

## Immediate implementation boundary

Adopting this ADR does not silently rewrite the existing skill.

The first repository restructuring pass SHALL:

- leave `confirm-with-pseudocode/SKILL.md` unchanged;
- leave the frozen behavioral harness unchanged;
- add this ADR and TRD-0002;
- add a runtime manifest for the current skill package;
- add a deterministic manifest verifier;
- integrate mechanical package verification into CI; and
- update installation and public architecture documentation.

Extraction of current skill instructions into stable-ID Standard Contracts is a
subsequent implementation phase and SHALL preserve the current confirmed
behavioral baseline.

## Consequences

### Positive

- Normative requirements gain one authoritative home.
- Repository search no longer needs to act as an implicit instruction source.
- Context projection can select explicit contracts instead of discovering prose.
- Prompt, Plan, Execution, and judge contexts become independently measurable.
- Mechanical, semantic, and human checks are represented honestly without
  pretending they have equal certainty.
- Partial package installation can be detected before the skill is invoked.
- Model-specific calibration can evolve without changing correctness.
- The controller can remain deterministic without taking semantic interpretation
  away from the model/user feedback loop.
- Future same-model, cross-model, and smaller-worker experiments share the same
  handoff and authority model.

### Negative

- More interfaces and stable IDs increase initial repository design work.
- Bad contract routing can omit required context.
- Semantic judges can produce false positives, false negatives, and correlated
  model-family biases.
- Source bindings require lifecycle and digest management.
- Maintaining a manifest introduces release discipline whenever runtime bytes
  change.
- Projected workers may add call overhead even when they reduce context replay.

## Alternatives considered

### Keep one monolithic skill/repository context

Rejected as the target architecture. It is simple to execute but allows
irrelevant repository material and conversation history to compete with the
active task context.

### Implement a generic deterministic verifier first

Rejected as the next primary milestone. Deterministic verification is necessary
for package identity, counts, schemas, and other objective invariants, but it
cannot detect the principal semantic execution-drift findings.

### Use only human-readable model checklists

Rejected as the complete verification mechanism. Checklists are useful as the
inspectable Verification Contract, but model execution of a checklist remains
probabilistic for semantic items and should not replace deterministic code for
mechanical predicates.

### Use only a fresh semantic judge

Rejected. A semantic judge cannot prove package identity, file completeness,
artifact digests, or state-transition facts, and must not become authoritative
for ambiguous user meaning.

### Build the full controller before contract extraction

Rejected as the next implementation step. The controller's most important
inputs are its context and authority contracts. Those interfaces should be
made explicit and experimentally validated before the full UI and persistence
layer hardens around them.

## Follow-up

TRD-0002 specifies the transition substrate, manifest format, mechanical
verifier, installation boundary, and interfaces that later projected workers
and the controller will consume.
