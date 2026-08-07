# ADR-0006: Bound pre-execution reasoning and material guessing

- Status: Accepted
- Date: 2026-08-06
- Parent decision: [ADR-0001](0001-controller-gated-pseudocode-protocol.md)
- Related requirements: [TRD-0001 Sections 10.1 and 10.2](../trd/0001-controller-gated-pseudocode-protocol.md#101-prompt-pseudocode)

## Context

Prompt interpretation and response planning do not require the substantive
reasoning needed to solve the user's task. Allowing full task analysis before
confirmation can leak answers into artifacts, anchor the later execution, and
spend tokens on an interpretation or approach the user may reject.

Eliminating reasoning entirely is also incorrect. Producing faithful
pseudocode requires bounded semantic work, including:

- resolving ordinary references and instruction relationships;
- preserving priorities, exclusions, conditions, and ordering;
- distinguishing a complete interpretation from a response strategy;
- producing valid structured English;
- checking that a plan is inspectable without predicting its result.

Natural language always requires some inference. Requiring clarification for
every possible interpretation would create excessive interruption and defeat
the purpose of the visible correction loop.

## Decision

Prompt and Plan phases SHALL use only the reasoning necessary to create and
validate their respective user-visible artifacts.

Before execution, the model SHALL NOT:

- solve the task;
- research substantive findings;
- calculate requested results;
- select winners or conclusions;
- invent missing requirements;
- silently improve the request;
- fill consequential gaps with speculative assumptions.

Ordinary semantic inference MAY be used when it produces one coherent,
inspectable interpretation without materially adding to the request. The
Prompt Pseudocode SHALL expose the interpretation actually formed so the user
can correct it.

When missing information prevents a coherent artifact or requires choosing
between materially different goals, scopes, output requirements, safety
postures, costs, or irreversible actions, the system SHALL request the smallest
targeted clarification needed. Clarification SHALL not become a general
ambiguity-enumeration DSL.

The controller SHOULD remove reasoning about protocol branching by presenting
explicit events. In particular, Plan review SHOULD distinguish **Revise
approach** from **Change request** rather than asking the model to guess which
kind of change the user intended.

This decision does not limit substantive reasoning during execution. After the
confirmed pair is available, the executor MAY use the reasoning effort required
to satisfy the request safely and correctly while remaining within the
confirmed plan.

## Consequences

### Positive

- Fewer tokens are spent solving rejected interpretations or plans.
- Prompt and Plan artifacts are less likely to contain premature conclusions.
- The user retains control over consequential assumptions.
- Ordinary requests are not interrupted by exhaustive ambiguity analysis.
- Execution reasoning begins from confirmed semantic and procedural boundaries.

### Negative

- The boundary between harmless inference and material guessing still requires
  semantic judgment.
- Excessively weak pre-execution reasoning can omit instruction relationships.
- Excessively aggressive clarification can create interaction fatigue.
- Model reasoning controls are provider-dependent and cannot replace behavioral
  validation.

## Alternatives considered

### Use no reasoning before execution

Rejected. Semantic interpretation, PDL generation, and plan-poisoning detection
cannot be performed reliably without any inference.

### Allow full analysis before confirmation

Rejected. It increases cost and permits findings to anchor or contaminate the
confirmation artifacts.

### Ask about every ambiguity

Rejected. The artifact correction loop is the normal ambiguity-resolution
mechanism; targeted clarification is reserved for materially blocking gaps.

