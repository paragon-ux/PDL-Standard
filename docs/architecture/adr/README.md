# Architecture decision records

| ADR | Status | Decision |
|---|---|---|
| [ADR-0001](0001-controller-gated-pseudocode-protocol.md) | Accepted | Adopt the umbrella controller-gated pseudocode protocol. |
| [ADR-0002](0002-controller-owned-artifact-controls.md) | Accepted | Put artifact UI and deterministic branching in the host controller. |
| [ADR-0003](0003-phase-projected-single-model-contexts.md) | Accepted | Use controller-compiled phase contexts with one model as the core baseline. |
| [ADR-0004](0004-confirmed-artifacts-as-execution-boundary.md) | Accepted | Execute from a clean projection containing the confirmed pair and required task inputs. |
| [ADR-0005](0005-optional-result-pseudocode.md) | Accepted | Offer Result Pseudocode as an optional execution-output mode. |
| [ADR-0006](0006-bounded-pre-execution-reasoning.md) | Accepted | Limit pre-execution reasoning and avoid materially consequential guessing. |
| [ADR-0007](0007-contract-governed-context-projected-runtime.md) | Accepted | Adopt contract-governed context projection, typed verification, and controller-owned authority as the target runtime architecture. |

ADR-0007 preserves the confirmed-artifact and controller-state decisions while
refining implementation priority: make normative/context contracts and narrow
mechanical verification explicit before hardening the full controller UI.
