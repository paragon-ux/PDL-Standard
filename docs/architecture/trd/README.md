# Technical requirements documents

| TRD | Status | Scope |
|---|---|---|
| [TRD-0001](0001-controller-gated-pseudocode-protocol.md) | Draft for implementation | Baseline host-controller lifecycle, canonical state, phase projection, artifact requirements, and Result Pseudocode mode. |
| [TRD-0002](0002-contract-substrate-and-mechanical-verification.md) | Draft for implementation | Contract governance, typed verification, runtime manifest, safe installation, source binding, and staged context-projected-worker migration. |

TRD-0002 does not replace the behavioral protocol in TRD-0001. It defines the
context, packaging, and verification substrate the later controller should
consume rather than reimplement.
